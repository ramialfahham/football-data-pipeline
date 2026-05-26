"""Per-fixture HTTP fanout: fetches and persists lineups, events, stats, players, predictions.

For every finished fixture (status FT/AET/PEN) we call five API endpoints and store
the results as appended rows in each RAW_* fanout table (one new row per run per
competition). Coverage — knowing which fixtures already have which endpoint data — is
tracked in RAW_APIF_FIXTURE_COVERAGE (see ingestion/api_football/coverage.py).

Selection is completeness-driven: before spending any quota we read the coverage table
and skip fixture_ids that are already covered per endpoint. A run therefore only pays
for work that actually advances completeness. This makes daily runs converge
monotonically without any operator intervention — re-run after a quota limit and it
picks up exactly where it left off.

Coverage flags (from GET /leagues) declare which endpoints a competition supports.
For statistics specifically, finished fixtures always get a fetch attempt regardless
of the coverage flag — the flag reflects the reference (latest) season, which for
upcoming tournaments may be false even though prior seasons have data.

Two fanout entry points:
- run_fixture_fanout_and_persist(): per-competition fanout (legacy, kept for ingest_league).
- run_global_fanout_and_persist(): global two-phase fanout across all competitions. Builds
  a shared priority queue (finished gaps oldest-first → upcoming nearest-first), applies
  one global budget, then persists per competition. Adding a new competition requires only
  a registry entry — no code changes here.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..coverage import (
    SHELL_KEY_TO_ENDPOINT,
    covered_for_league,
    read_coverage,
    write_coverage,
)
from ..settings import raw_league_table
from ..fixture_scheduling import (
    # Re-exported for backward compatibility (tests import from this module).
    _FANOUT_ENTITY_KEYS,
    _fixture_needs_any_endpoint,
    # Global fanout helpers.
    CompetitionFanoutInput,
    build_global_fanout_queue,
    _budgeted_global_fanout_ids,
    _fixture_kickoff_by_id,
    # Per-competition fanout helpers (legacy path).
    _budgeted_fixture_fanout_ids,
    _fanout_fixture_order,
    _write_fanout_cursor,
)
from ..http_client import fetch_json
from ..merge import merge_fanout_batched
from ..quota import append_api_errors
from .context import CompetitionRunResult, PipelineContext


def _batched_shell(league_code: str) -> dict[str, dict]:
    """Create an empty response accumulator for each of the five fanout endpoints.

    Each shell is a dict with the same structure as an API envelope: a league_code
    field and an empty response list. As fixtures are fetched, their data is
    appended to the relevant shell's response list. The shell is then written to
    BigQuery at the end of the run.
    """
    base = {"league_code": league_code, "response": []}
    return {key: dict(base) for key, _entity, _cov_key in _FANOUT_ENTITY_KEYS}


def _fanout_fetch_json(
    ctx: PipelineContext,
    path: str,
    params: dict,
    error_label: str,
) -> dict | None:
    """Call one API endpoint and return the JSON response.

    Returns None (without appending to the shell) when the daily quota is
    already exhausted — this short-circuits the fetch loop so we don't make
    API calls that will be rejected.
    """
    if errors_quota._http_quota_exhausted:
        return None
    data = fetch_json(path, headers=ctx.headers, params=params)
    append_api_errors(data, error_label, ctx.errors)
    return data


def _finished_fixture_ids(fixtures_response: list[dict]) -> set[int]:
    """Extract fixture IDs whose status is FT, AET, or PEN (the match has ended)."""
    finished: set[int] = set()
    for row in fixtures_response or []:
        fixture = row.get("fixture") or {}
        status_short = ((fixture.get("status") or {}).get("short") or "").strip().upper()
        if status_short not in {"FT", "AET", "PEN"}:
            continue
        fixture_id = fixture.get("id")
        if fixture_id is None:
            continue
        try:
            finished.add(int(fixture_id))
        except (TypeError, ValueError):
            continue
    return finished


def _persist_fanout_and_coverage(
    ctx: PipelineContext,
    league_code: str,
    shells: dict[str, dict],
) -> None:
    """Write this run's fanout data to raw tables and record coverage.

    For each of the five endpoints:
      1. If new rows were fetched this run, append them to the raw fanout table.
         (Each run appends one row per competition per endpoint that had new data.)
      2. Write a coverage record to RAW_APIF_FIXTURE_COVERAGE for each
         (league_code, fixture_id, endpoint) combination that was attempted.

    For FIXTURE_STATISTICS, coverage is written on every fetch attempt (empty or
    not) with has_data=True/False. An empty response (has_data=False) will be
    retried on subsequent runs within STATS_GRACE_DAYS of the fixture's kickoff
    date; after that the entry is treated as permanent and no further quota is
    spent. For all other endpoints, has_data is always True (any response counts).
    """
    coverage_rows: list[dict] = []

    for key, entity, _cov_key in _FANOUT_ENTITY_KEYS:
        shell = shells[key]
        new_rows = shell.get("response") or []

        if not new_rows:
            # Nothing fetched for this endpoint this run — skip write.
            continue

        try:
            tbl = raw_league_table(league_code, entity)
            load_json_to_bq(
                ctx.client,
                tbl,
                shell,
                as_json_payload=True,
                append=True,
            )
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"{entity.lower()} BQ {league_code}: {e}")
            continue

        # Build coverage rows for all fixtures fetched for this endpoint.
        endpoint_name = SHELL_KEY_TO_ENDPOINT[key]
        payload_key = {
            "lineups":    "lineups",
            "events":     "events",
            "fx_stats":   "statistics",
            "fx_players": "players",
            "preds":      "predictions",
        }[key]

        for row in new_rows:
            fid = row.get("fixture_id")
            if fid is None:
                continue

            if endpoint_name == "FIXTURE_STATISTICS":
                # Always write a coverage row — has_data records whether this fetch
                # delivered actual statistics. An empty response (has_data=False) will
                # be retried within STATS_GRACE_DAYS of the fixture's kickoff date;
                # after that grace period the entry is treated as permanent and the
                # fixture stops consuming daily quota.
                has_data = bool(row.get(payload_key))
            else:
                # Other endpoints: any successful fetch counts as covered.
                has_data = True

            coverage_rows.append({
                "league_code": league_code,
                "fixture_id":  int(fid),
                "endpoint":    endpoint_name,
                "has_data":    has_data,
            })

    # Write all coverage rows for this competition in one batch.
    if coverage_rows:
        try:
            write_coverage(ctx.client, coverage_rows)
        except Exception as e:
            ctx.errors.append(f"coverage write {league_code}: {e}")


def _fetch_fixture_endpoints(
    ctx: PipelineContext,
    league_code: str,
    fixture_id: int,
    covered: dict[str, set[int]],
    cov: dict[str, bool],
    finished_fixture_ids: set[int],
    sh: dict[str, dict],
) -> None:
    """Make HTTP calls for one fixture's missing endpoints and accumulate into shells.

    `covered` is a dict keyed by shell key (lineups, events, fx_stats, fx_players,
    preds), each mapping to the set of fixture IDs already fetched for that endpoint.
    An endpoint is skipped when the fixture ID is already in the covered set.
    """
    if cov.get("fixture_lineups", True) and fixture_id not in covered["lineups"]:
        try:
            lineups = _fanout_fetch_json(
                ctx,
                "/fixtures/lineups",
                {"fixture": fixture_id},
                f"lineups {league_code} fixture {fixture_id}",
            )
            if lineups is not None:
                sh["lineups"]["response"].append(
                    {"fixture_id": fixture_id, "lineups": lineups.get("response", [])}
                )
        except Exception as e:
            ctx.errors.append(f"lineups {league_code} fixture {fixture_id}: {e}")

    if cov.get("fixture_events", True) and fixture_id not in covered["events"]:
        try:
            ev = _fanout_fetch_json(
                ctx,
                "/fixtures/events",
                {"fixture": fixture_id},
                f"fixtures/events {league_code} fixture {fixture_id}",
            )
            if ev is not None:
                sh["events"]["response"].append(
                    {"fixture_id": fixture_id, "events": ev.get("response", [])}
                )
        except Exception as e:
            ctx.errors.append(f"fixtures/events {league_code} fixture {fixture_id}: {e}")

    if (cov.get("fixture_statistics", True) or fixture_id in finished_fixture_ids) and fixture_id not in covered["fx_stats"]:
        try:
            fxs = _fanout_fetch_json(
                ctx,
                "/fixtures/statistics",
                {"fixture": fixture_id},
                f"fixtures/statistics {league_code} fixture {fixture_id}",
            )
            if fxs is not None:
                sh["fx_stats"]["response"].append(
                    {"fixture_id": fixture_id, "statistics": fxs.get("response", [])}
                )
        except Exception as e:
            ctx.errors.append(
                f"fixtures/statistics {league_code} fixture {fixture_id}: {e}"
            )

    if cov.get("fixture_players", True) and fixture_id not in covered["fx_players"]:
        try:
            fxp = _fanout_fetch_json(
                ctx,
                "/fixtures/players",
                {"fixture": fixture_id},
                f"fixtures/players {league_code} fixture {fixture_id}",
            )
            if fxp is not None:
                sh["fx_players"]["response"].append(
                    {"fixture_id": fixture_id, "players": fxp.get("response", [])}
                )
        except Exception as e:
            ctx.errors.append(
                f"fixtures/players {league_code} fixture {fixture_id}: {e}"
            )

    if cov.get("predictions", True) and fixture_id not in covered["preds"]:
        try:
            pr = _fanout_fetch_json(
                ctx,
                "/predictions",
                {"fixture": fixture_id},
                f"predictions {league_code} fixture {fixture_id}",
            )
            if pr is not None:
                sh["preds"]["response"].append(
                    {"fixture_id": fixture_id, "predictions": pr.get("response", [])}
                )
        except Exception as e:
            ctx.errors.append(f"predictions {league_code} fixture {fixture_id}: {e}")


def run_global_fanout_and_persist(
    ctx: PipelineContext,
    results: list[CompetitionRunResult],
) -> None:
    """Global completeness-driven fanout across all competitions.

    Algorithm:
    1. Read the coverage table ONCE to learn which fixture-endpoint combinations
       have already been fetched across all competitions.
    2. Build a global priority queue: finished fixtures missing data (oldest first) →
       upcoming fixtures missing data (nearest first).
    3. Apply global budget via _budgeted_global_fanout_ids.
    4. Fetch missing endpoints competition-by-competition within the budget.
    5. Persist raw rows and write new coverage records per competition.

    This guarantees:
    - Historical gaps are filled monotonically, oldest fixtures first.
    - New matchday fixtures stay fresh (upcoming tier).
    - Budget is never wasted — if a competition is 100% complete it contributes nothing
      to the queue and consumes no quota.
    - Adding a new competition requires only a registry entry.
    """
    # Step 1: read coverage table once for all competitions.
    # This replaces the old pattern of reading one merged blob per endpoint per
    # competition (5 blobs × N competitions = many BQ reads). Now it is one query.
    all_covered = read_coverage(ctx.client)

    inputs: list[CompetitionFanoutInput] = []
    covered_by_lc: dict[str, dict[str, set[int]]] = {}
    finished_by_lc: dict[str, set[int]] = {}
    cov_by_lc: dict[str, dict[str, bool]] = {}

    for result in results:
        kickoff_by_id = _fixture_kickoff_by_id(result.fixtures_merged.get("response", []))
        # Translate coverage table format (endpoint names) to fanout shell keys.
        # Pass kickoff_by_id so the grace-period logic can determine whether
        # FIXTURE_STATISTICS fixtures with has_data=False should be retried.
        covered = covered_for_league(all_covered, result.league_code, kickoff_by_id=kickoff_by_id)
        covered_by_lc[result.league_code] = covered
        finished_ids = _finished_fixture_ids(result.fixtures_merged.get("response", []))
        finished_by_lc[result.league_code] = finished_ids
        cov_by_lc[result.league_code] = result.cov
        inputs.append(CompetitionFanoutInput(
            league_code=result.league_code,
            fixture_ids=result.fixture_ids,
            covered=covered,
            cov=result.cov,
            kickoff_by_id=kickoff_by_id,
            finished_fixture_ids=finished_ids,
        ))

    # Step 2: build global queue
    queue = build_global_fanout_queue(inputs)
    total_missing = len(queue)

    missing_by_lc: dict[str, int] = {}
    for inp in inputs:
        missing_by_lc[inp.league_code] = sum(
            1 for fid in inp.fixture_ids
            if _fixture_needs_any_endpoint(fid, inp.covered, inp.cov, inp.finished_fixture_ids)
        )
    summary = " ".join(
        f"{lc}:{missing_by_lc.get(lc, 0)}" for lc in (r.league_code for r in results)
    )
    print(
        f"[api-football] global_fanout total_missing={total_missing} per_competition={summary}",
        flush=True,
    )

    # Step 3: apply global budget
    all_team_ids: set[int] = set()
    for result in results:
        all_team_ids |= result.team_ids
    budgeted = _budgeted_global_fanout_ids(queue, all_team_ids, ctx.errors)

    # Step 4: fetch — accumulate results per competition
    shells_by_lc = {r.league_code: _batched_shell(r.league_code) for r in results}

    for league_code, fixture_id in budgeted:
        if errors_quota._http_quota_exhausted:
            break
        _fetch_fixture_endpoints(
            ctx,
            league_code,
            fixture_id,
            covered_by_lc[league_code],
            cov_by_lc[league_code],
            finished_by_lc[league_code],
            shells_by_lc[league_code],
        )

    # Step 5: persist raw rows and write coverage for each competition
    for result in results:
        _persist_fanout_and_coverage(
            ctx, result.league_code, shells_by_lc[result.league_code]
        )


def run_fixture_fanout_and_persist(
    ctx: PipelineContext,
    league_code: str,
    fixtures_merged: dict,
    fixture_ids: set[int],
    team_ids: set[int],
    cov: dict[str, bool],
) -> None:
    """Legacy per-competition fanout. Used by ingest_league() only."""
    ordered_fanout, chrono_all, cursor_start = _fanout_fixture_order(
        ctx.client,
        fixtures_merged.get("response", []),
        fixture_ids,
        league_code,
        ctx.errors,
    )

    # Read coverage for this competition from the coverage table.
    all_covered = read_coverage(ctx.client)
    kickoff_by_id = _fixture_kickoff_by_id(fixtures_merged.get("response", []))
    covered = covered_for_league(all_covered, league_code, kickoff_by_id=kickoff_by_id)

    finished_fixture_ids = _finished_fixture_ids(fixtures_merged.get("response", []))
    ordered_missing = [
        fid for fid in ordered_fanout
        if _fixture_needs_any_endpoint(fid, covered, cov, finished_fixture_ids)
    ]
    missing_index = {fixture_id: idx for idx, fixture_id in enumerate(ordered_missing)}
    ordered_missing = sorted(
        ordered_missing,
        key=lambda fixture_id: (
            0
            if (
                fixture_id in finished_fixture_ids
                and fixture_id not in covered["fx_stats"]
            )
            else 1,
            missing_index[fixture_id],
        ),
    )

    print(
        f"[api-football] fanout_selection league={league_code} "
        f"target={len(fixture_ids)} "
        f"already_complete={len(fixture_ids) - len(ordered_missing)} "
        f"missing_any_endpoint={len(ordered_missing)}"
    )

    fanout_ids = _budgeted_fixture_fanout_ids(
        ordered_missing, team_ids, league_code, ctx.errors
    )
    sh = _batched_shell(league_code)

    for fixture_id in fanout_ids:
        if errors_quota._http_quota_exhausted:
            break
        _fetch_fixture_endpoints(ctx, league_code, fixture_id, covered, cov, finished_fixture_ids, sh)

    pri = os.getenv("API_FOOTBALL_FANOUT_PRIORITY", "upcoming").strip().lower()
    if pri == "cursor" and chrono_all and cursor_start is not None:
        try:
            new_off = (cursor_start + len(fanout_ids)) % max(len(chrono_all), 1)
            _write_fanout_cursor(ctx.client, league_code, new_off, len(chrono_all))
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"ingest_cursor {league_code}: {e}")

    _persist_fanout_and_coverage(ctx, league_code, sh)
