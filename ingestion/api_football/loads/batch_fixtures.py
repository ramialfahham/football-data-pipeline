"""Batch fixture ingestion: full sub-data via GET /fixtures?ids=ID1-...-ID20.

Step 2 of the documented two-step ingestion pattern (Step 1 is loads/fixtures.py).
One API call per 20 finished fixtures returns events, lineups, statistics, and players
embedded in the response — replacing the old 5-endpoint-per-fixture fanout.

Coverage is derived by querying RAW_APIF_{LC}_FIXTURE_DETAILS: any fixture_id already
present in that table with non-empty statistics is considered done. Fixtures with empty
statistics are retried for up to STATS_RETRY_DAYS days after kickoff (API-Football
documents up to a 48-hour delay for non-livescore leagues); after that they are accepted
as permanently empty and not retried.

Rate limiting: the Pro plan allows 300 calls/min burst. Sleeping API_FOOTBALL_BATCH_SLEEP_MS
(default 250 ms) between calls gives ~4 calls/sec, safely under the limit. This sleep is
separate from the general API_FOOTBALL_REQUEST_PAUSE_MS throttle used by other API calls.
Synchronous HTTP only — the API ToS permanently bans IPs that use async/threading.

See docs/api_football_ingestion_blueprint.md for the full API specification.
"""

from __future__ import annotations

import time
from datetime import date, timedelta

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..http_client import fetch_json
from ..quota import append_api_errors
from ..settings import GCP_PROJECT_ID, DATASET_ID, _env_int, raw_league_table
from .context import CompetitionRunResult, PipelineContext

# API-Football documented limit: up to 20 fixture IDs per /fixtures?ids=... call.
_BATCH_SIZE = 20

# Retry fixtures with empty statistics for this many days after kickoff.
# The API documents up to 48 hours delay; 3 days gives one extra day of buffer.
_STATS_RETRY_DAYS = 3


def _fixture_details_table_id(league_code: str) -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_league_table(league_code, 'FIXTURE_DETAILS')}"


def _read_fetched_coverage(
    client: bigquery.Client,
    league_code: str,
) -> dict[int, bool]:
    """Return {fixture_id: has_statistics} for all fixtures in RAW_APIF_{LC}_FIXTURE_DETAILS.

    has_statistics is True if at least one stored row for this fixture contained a
    non-empty statistics array. Returns an empty dict when the table does not exist
    (first run for this competition — all finished fixtures will be fetched).
    """
    table_id = _fixture_details_table_id(league_code)
    try:
        client.get_table(table_id)
    except NotFound:
        return {}

    q = f"""
        SELECT
          CAST(JSON_VALUE(item, '$.fixture.id') AS INT64) AS fixture_id,
          LOGICAL_OR(ARRAY_LENGTH(JSON_QUERY_ARRAY(item, '$.statistics')) > 0)
            AS has_statistics
        FROM `{table_id}`,
        UNNEST(JSON_QUERY_ARRAY(payload, '$.response')) AS item
        WHERE JSON_VALUE(item, '$.fixture.id') IS NOT NULL
        GROUP BY 1
    """
    try:
        rows = list(client.query(q).result())
    except Exception:
        return {}

    return {
        int(row.fixture_id): bool(row.has_statistics)
        for row in rows
        if row.fixture_id is not None
    }


def _needs_fetch(
    fixture_id: int,
    fetched: dict[int, bool],
    kickoff_by_id: dict[int, date],
    retry_cutoff: date,
) -> bool:
    """Return True if this finished fixture needs a (re-)fetch.

    Decision table:
      Never fetched                           → fetch
      Fetched, statistics non-empty           → skip (done permanently)
      Fetched, statistics empty, within window → retry (delivery delay expected)
      Fetched, statistics empty, past window  → skip (accept empty permanently)
      Fetched, statistics empty, no kickoff   → skip (can't determine window)
    """
    if fixture_id not in fetched:
        return True
    if fetched[fixture_id]:
        return False  # statistics present — done
    # Empty statistics — retry only within the 3-day window from kickoff.
    kickoff = kickoff_by_id.get(fixture_id)
    if kickoff is None:
        return False
    return kickoff >= retry_cutoff


def _finished_fixture_ids(fixtures_response: list[dict]) -> set[int]:
    """Return fixture IDs whose status is FT, AET, or PEN (match has ended)."""
    out: set[int] = set()
    for row in fixtures_response or []:
        fx = row.get("fixture") or {}
        short = ((fx.get("status") or {}).get("short") or "").strip().upper()
        if short not in {"FT", "AET", "PEN"}:
            continue
        fid = fx.get("id")
        if fid is None:
            continue
        try:
            out.add(int(fid))
        except (TypeError, ValueError):
            continue
    return out


def _fetch_and_persist_batch(
    ctx: PipelineContext,
    league_code: str,
    fixture_ids: list[int],
) -> None:
    """Call GET /fixtures?ids=... for one batch and append the response.

    The full API response (events, lineups, statistics, players for each fixture)
    is appended as one new row to RAW_APIF_{LC}_FIXTURE_DETAILS.
    """
    ids_param = "-".join(str(fid) for fid in fixture_ids)
    data = fetch_json("/fixtures", headers=ctx.headers, params={"ids": ids_param})
    append_api_errors(data, f"fixture_details {league_code}", ctx.errors)

    table_name = raw_league_table(league_code, "FIXTURE_DETAILS")
    load_json_to_bq(ctx.client, table_name, data, as_json_payload=True, append=True)
    ctx.add_loaded(1)


def run_batch_fixture_fanout_and_persist(
    ctx: PipelineContext,
    results: list[CompetitionRunResult],
) -> None:
    """Fetch full sub-data for all finished fixtures across all competitions.

    Two-step process per competition:
      1. Read RAW_APIF_{LC}_FIXTURE_DETAILS to determine which finished fixtures
         already have good statistics. Fixtures missing entirely or with empty stats
         within the 3-day retry window are queued for fetching.
      2. Batch-fetch 20 fixture IDs at a time via GET /fixtures?ids=ID1-...-ID20.
         Each response is appended to RAW_APIF_{LC}_FIXTURE_DETAILS.

    All competitions are planned before any HTTP calls are made, so the printed
    summary reflects the full picture before quota is spent.
    """
    from ..fixture_scheduling import _fixture_kickoff_by_id

    today = date.today()
    retry_cutoff = today - timedelta(days=_STATS_RETRY_DAYS)
    sleep_s = _env_int("API_FOOTBALL_BATCH_SLEEP_MS", 250) / 1000.0

    # -----------------------------------------------------------------------
    # Planning pass — determine what needs fetching for each competition.
    # No HTTP calls yet.
    # -----------------------------------------------------------------------
    plan: list[tuple[str, list[int]]] = []
    for result in results:
        response = result.fixtures_merged.get("response", [])
        finished = _finished_fixture_ids(response)
        kickoff_by_id = _fixture_kickoff_by_id(response)
        fetched = _read_fetched_coverage(ctx.client, result.league_code)

        to_fetch = sorted(
            fid for fid in finished
            if _needs_fetch(fid, fetched, kickoff_by_id, retry_cutoff)
        )

        n_done = len(finished) - len(to_fetch)
        print(
            f"[api-football] batch_fanout league={result.league_code} "
            f"finished={len(finished)} done={n_done} to_fetch={len(to_fetch)}",
            flush=True,
        )
        if to_fetch:
            plan.append((result.league_code, to_fetch))

    total_fixtures = sum(len(ids) for _, ids in plan)
    total_calls = sum(
        (len(ids) + _BATCH_SIZE - 1) // _BATCH_SIZE for _, ids in plan
    )
    print(
        f"[api-football] batch_fanout total_fixtures_to_fetch={total_fixtures} "
        f"total_api_calls={total_calls}",
        flush=True,
    )

    # -----------------------------------------------------------------------
    # Fetch pass — one batch at a time, sleeping between calls.
    # -----------------------------------------------------------------------
    first_call = True
    for league_code, fixture_ids in plan:
        for i in range(0, len(fixture_ids), _BATCH_SIZE):
            if errors_quota._http_quota_exhausted:
                return
            batch = fixture_ids[i : i + _BATCH_SIZE]
            if not first_call and sleep_s > 0:
                time.sleep(sleep_s)
            first_call = False
            try:
                _fetch_and_persist_batch(ctx, league_code, batch)
            except Exception as e:
                ctx.errors.append(f"batch_fixtures {league_code}: {e}")
