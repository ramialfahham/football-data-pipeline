"""Ask the provider again for named matches or team-seasons, and append the answers to raw.

fixtures: GET /fixtures?ids= (20 a call) for every match in --ids-file (CSV: league_code,fixture_id).
A match is written only when its new answer holds two line-ups of eleven starters and is no worse
than any stored fetch of it: no fewer events, no fewer player rows or statistics lines for either
team, and not losing the complete player format. Base takes the latest events fetch whole, so a
shorter answer would replace a longer one. The stored counts come from the staging tables, so a run
is refused while raw holds a row for a listed match that staging has not read yet.

squads: GET /players?team=&season= for every pair in --pairs-file (CSV: league_code,team_id,season),
through the nightly's own loader. Base unions every squad fetch, so the loader's incomplete-fetch
guard is the only one needed.

Plans by default and makes no call. --run fetches and writes, holding the ingest lock for a lease
of LEASE_MINUTES, and makes no call after CALL_WINDOW_MINUTES of it. It stops at --max-calls and on
the provider's daily limit, and refuses to start between 02:00 and 04:00 UTC, so a lease left by a
killed run ends before the nightly starts.

    python scripts/refetch_from_provider.py fixtures --ids-file <csv>
    python scripts/refetch_from_provider.py fixtures --ids-file <csv> --run --max-calls 260
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from google.cloud import bigquery

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ingestion.api_football import http_client  # noqa: E402
from ingestion.api_football import quota as errors_quota  # noqa: E402
from ingestion.api_football.bigquery import ensure_unified_raw_table  # noqa: E402
from ingestion.api_football.http_client import fetch_json, result_is_complete  # noqa: E402
from ingestion.api_football.ingestion_lock import (  # noqa: E402
    acquire_ingest_lock,
    ensure_ingest_lock_table,
    new_run_id,
    release_ingest_lock,
)
from ingestion.api_football.loads.batch_fixtures import (  # noqa: E402
    _BATCH_SIZE,
    _insert_fixture_rows,
)
from ingestion.api_football.loads.context import PipelineContext  # noqa: E402
from ingestion.api_football.loads.squads import load_squad_players_batch  # noqa: E402
from ingestion.api_football.quota import append_api_errors  # noqa: E402
from ingestion.api_football.settings import (  # noqa: E402
    DATASET_ID,
    GCP_PROJECT_ID,
    _env_int,
    get_headers,
    raw_table,
)

LEASE_MINUTES = 60
CALL_WINDOW_MINUTES = 50
STAGING_TABLES = ("stg_apif__fixture_events", "stg_apif__fixture_players", "stg_apif__fixture_statistics")


def read_fixture_list(path: str) -> dict[str, list[int]]:
    groups: dict[str, set[int]] = defaultdict(set)
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            groups[row["league_code"].strip()].add(int(row["fixture_id"]))
    return {league: sorted(ids) for league, ids in sorted(groups.items())}


def read_pair_list(path: str) -> dict[tuple[str, int], set[int]]:
    groups: dict[tuple[str, int], set[int]] = defaultdict(set)
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            groups[(row["league_code"].strip(), int(row["season"]))].add(int(row["team_id"]))
    return dict(sorted(groups.items()))


def fixture_calls(groups: dict[str, list[int]]) -> int:
    return sum(math.ceil(len(ids) / _BATCH_SIZE) for ids in groups.values())


def squad_calls(groups: dict[tuple[str, int], set[int]], max_pages: int) -> int:
    return sum(len(teams) for teams in groups.values()) * max_pages


def too_close_to_nightly(now: datetime) -> bool:
    return 2 <= now.astimezone(timezone.utc).hour < 4


def _team_id(block: dict) -> int:
    return int((block.get("team") or {}).get("id") or 0)


def payload_counts(fx: dict) -> dict:
    player_blocks = fx.get("players") or []
    players = [p for t in player_blocks for p in (t.get("players") or [])]
    lineups = fx.get("lineups") or []
    return {
        "events": len(fx.get("events") or []),
        "players_by_team": {_team_id(t): len(t.get("players") or []) for t in player_blocks},
        "players_complete": any(
            (((p.get("statistics") or [{}])[0] or {}).get("goals") or {}).get("conceded") is not None
            for p in players
        ),
        "statistics_by_team": {_team_id(t): len(t.get("statistics") or []) for t in fx.get("statistics") or []},
        "full_lineups": len(lineups) == 2
        and all(len(lu.get("startXI") or []) == 11 for lu in lineups),
    }


def refusal_reasons(new: dict, stored: dict | None) -> list[str]:
    reasons = []
    if not new["full_lineups"]:
        reasons.append("no two line-ups of eleven starters")
    if stored is None:
        return reasons
    if new["events"] < stored["events"]:
        reasons.append(f"fewer events ({new['events']} < {stored['events']})")
    for key, label in (("players_by_team", "player rows"), ("statistics_by_team", "statistics lines")):
        for team, n_stored in sorted(stored[key].items()):
            n_new = new[key].get(team, 0)
            if n_new < n_stored:
                reasons.append(f"fewer {label} for team {team} ({n_new} < {n_stored})")
    if stored["players_complete"] and not new["players_complete"]:
        reasons.append("loses the complete player format")
    return reasons


_STORED_SQL = """
with events as (
    select fixture_id, raw_ingested_at, count(*) as n
    from `{p}.staging.stg_apif__fixture_events`
    where fixture_id in unnest(@ids)
    group by 1, 2
),
players as (
    select fixture_id, team_id, raw_ingested_at, count(*) as n, logical_or(goals_against is not null) as complete
    from `{p}.staging.stg_apif__fixture_players`
    where fixture_id in unnest(@ids)
    group by 1, 2, 3
),
statistics as (
    select fixture_id, team_id, raw_ingested_at, count(*) as n
    from `{p}.staging.stg_apif__fixture_statistics`
    where fixture_id in unnest(@ids)
    group by 1, 2, 3
)
select 'events' as section, fixture_id, cast(null as int64) as team_id, max(n) as n, false as complete
from events group by 2
union all
select 'players', fixture_id, team_id, max(n), logical_or(complete) from players group by 2, 3
union all
select 'statistics', fixture_id, team_id, max(n), false from statistics group by 2, 3
"""


def stored_counts(client: bigquery.Client, fixture_ids: list[int]) -> dict[int, dict]:
    job = client.query(
        _STORED_SQL.format(p=GCP_PROJECT_ID),
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("ids", "INT64", fixture_ids)]
        ),
    )
    out = {
        fid: {"events": 0, "players_by_team": {}, "statistics_by_team": {}, "players_complete": False}
        for fid in fixture_ids
    }
    for r in job.result():
        stored = out[int(r["fixture_id"])]
        if r["section"] == "events":
            stored["events"] = int(r["n"])
        elif r["section"] == "players":
            stored["players_by_team"][int(r["team_id"] or 0)] = int(r["n"])
            stored["players_complete"] = stored["players_complete"] or bool(r["complete"])
        else:
            stored["statistics_by_team"][int(r["team_id"] or 0)] = int(r["n"])
    print(f"stored counts read: {job.total_bytes_billed or 0} bytes billed", flush=True)
    return out


def unread_raw_rows(client: bigquery.Client, fixture_ids: list[int]) -> int:
    """Listed matches with a raw row newer than the oldest of the staging tables the guard reads."""
    built = min(client.get_table(f"{GCP_PROJECT_ID}.staging.{t}").modified for t in STAGING_TABLES)
    job = client.query(
        f"""
        select count(distinct fixture_id) as n
        from `{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table("FIXTURE_DETAILS")}`
        where fixture_id in unnest(@ids) and ingested_at > @built
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("ids", "INT64", fixture_ids),
                bigquery.ScalarQueryParameter("built", "TIMESTAMP", built),
            ]
        ),
    )
    return int(next(iter(job.result()))["n"])


class _CapReached:
    status_code = 200

    def __init__(self) -> None:
        self.headers: dict = {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"errors": {"call_cap": "the run's call cap or call window is reached"}, "response": []}


class CallCounter:
    """Counts every HTTP call, retries included, and makes none past the cap or the deadline.

    The call refused is answered with a body-level error and latches the daily-limit flag, so
    result_is_complete turns false, fetch_json makes no further call, and the loaders write nothing
    they did not finish.
    """

    def __init__(self, max_calls: int, deadline: datetime | None = None):
        self.max_calls = max_calls
        self.deadline = deadline
        self.calls = 0
        self._get = http_client.requests.get

    def get(self, *args, **kwargs):
        past_deadline = self.deadline is not None and datetime.now(timezone.utc) >= self.deadline
        if self.calls >= self.max_calls or past_deadline:
            errors_quota._http_quota_exhausted = True
            return _CapReached()
        self.calls += 1
        return self._get(*args, **kwargs)

    def install(self) -> None:
        http_client.requests.get = self.get


def run_fixtures(ctx: PipelineContext, groups: dict[str, list[int]], stored: dict[int, dict]) -> dict:
    table_name = raw_table("FIXTURE_DETAILS")
    ensure_unified_raw_table(ctx.client, table_name, include_fixture_id=True)
    report = {"written": 0, "not_returned": 0, "batches_discarded": 0, "refused": defaultdict(int)}
    for league_code, ids in groups.items():
        for start in range(0, len(ids), _BATCH_SIZE):
            if errors_quota._http_quota_exhausted:
                return report
            batch = ids[start:start + _BATCH_SIZE]
            data = fetch_json("/fixtures", headers=ctx.headers, params={"ids": "-".join(map(str, batch))})
            append_api_errors(data, f"refetch fixture_details {league_code}", ctx.errors)
            if not result_is_complete(data):
                report["batches_discarded"] += 1
                continue
            returned = {int((fx.get("fixture") or {}).get("id") or 0): fx for fx in data.get("response") or []}
            report["not_returned"] += len(set(batch) - set(returned))
            kept = []
            for fid, fx in returned.items():
                reasons = refusal_reasons(payload_counts(fx), stored.get(fid))
                for reason in reasons:
                    report["refused"][reason.split(" (")[0].split(" for team")[0]] += 1
                if not reasons:
                    kept.append(fx)
            if kept:
                _insert_fixture_rows(ctx.client, table_name, kept, datetime.now(timezone.utc), league_code)
                report["written"] += len(kept)
    return report


def run_squads(ctx: PipelineContext, groups: dict[tuple[str, int], set[int]]) -> None:
    for (league_code, season), team_ids in groups.items():
        if errors_quota._http_quota_exhausted:
            return
        load_squad_players_batch(
            ctx,
            league_code,
            [season],
            set(team_ids),
            reference_season=season,
            already_captured=set(),
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=["fixtures", "squads"])
    parser.add_argument("--ids-file")
    parser.add_argument("--pairs-file")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--max-calls", type=int)
    args = parser.parse_args(argv)

    if args.mode == "fixtures":
        if not args.ids_file:
            parser.error("fixtures needs --ids-file")
        groups = read_fixture_list(args.ids_file)
        n_items = sum(len(ids) for ids in groups.values())
        planned = fixture_calls(groups)
        print(f"plan: {n_items} matches in {len(groups)} competitions, {planned} calls", flush=True)
    else:
        if not args.pairs_file:
            parser.error("squads needs --pairs-file")
        groups = read_pair_list(args.pairs_file)
        max_pages = _env_int("API_FOOTBALL_PLAYERS_MAX_PAGE", 3)
        n_items = sum(len(teams) for teams in groups.values())
        planned = squad_calls(groups, max_pages)
        print(f"plan: {n_items} team-seasons, at most {planned} calls ({max_pages} pages each)", flush=True)

    if not args.run:
        return 0
    if args.max_calls is None:
        parser.error("--run needs --max-calls")
    if too_close_to_nightly(datetime.now(timezone.utc)):
        print("refused: a run started between 02:00 and 04:00 UTC could still hold the lock at the nightly's start")
        return 2

    os.environ.setdefault("API_FOOTBALL_REQUEST_PAUSE_MS", "250")
    headers = get_headers()
    client = bigquery.Client(project=GCP_PROJECT_ID)
    fixture_ids = [fid for ids in groups.values() for fid in ids] if args.mode == "fixtures" else []
    ensure_ingest_lock_table(client)
    run_id = new_run_id()
    if not acquire_ingest_lock(client, run_id, lease_minutes=LEASE_MINUTES):
        print(f"refused: another ingest holds the lock ({GCP_PROJECT_ID}.{DATASET_ID}.RAW_APIF_INGEST_LOCK)")
        return 2
    try:
        if fixture_ids:
            unread = unread_raw_rows(client, fixture_ids)
            if unread:
                print(f"refused: raw holds {unread} listed matches newer than the staging build; rebuild staging first")
                return 2
        deadline = datetime.now(timezone.utc) + timedelta(minutes=CALL_WINDOW_MINUTES)
        counter = CallCounter(args.max_calls, deadline)
        counter.install()
        ctx = PipelineContext(client=client, headers=headers)
        if args.mode == "fixtures":
            stored = stored_counts(client, fixture_ids)
            report = run_fixtures(ctx, groups, stored)
            print(
                f"done: {counter.calls} calls, {report['written']} matches written, "
                f"{report['not_returned']} not returned, {report['batches_discarded']} batches discarded",
                flush=True,
            )
            for reason, n in sorted(report["refused"].items()):
                print(f"  refused, {reason}: {n}", flush=True)
        else:
            run_squads(ctx, groups)
            print(
                f"done: {counter.calls} calls, {ctx.tables_loaded} of {len(groups)} competition-seasons written",
                flush=True,
            )
        print(f"quota left: {errors_quota._last_requests_remaining}", flush=True)
        for err in ctx.errors:
            print(f"  error: {err}", flush=True)
    finally:
        release_ingest_lock(client, run_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
