"""Fetch /players/squads per team (batched) → RAW_APIF_SQUADS.

The current squad of each team (id, name, age, number, position, photo) in one call per
team. Distinct from loads/squads.py, which pulls /players per team×season into
RAW_APIF_PLAYERS (season roster + stats); this is the cheaper present-day squad endpoint and
is the only one that carries the shirt number. Each run appends a fresh complete snapshot row
per league. No cross-run merge with prior BQ data.

The snapshot is stamped with the team's last-recorded ``season`` so per-season coverage is exact
and the raw row is self-describing. Two capture paths feed this table:
- in-season (Phase 3b): full-mode comps capture every run;
- catch-up (Phase 3c): finished (poll-mode) comps whose teams are not already covered for that
  season — keyed by team, deduped across comps, club and national teams alike. See
  ``select_squad_catchup_team_ids`` / ``captured_team_seasons``.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import DATASET_ID, GCP_PROJECT_ID, raw_table
from ..fixture_scheduling import squads_response_for_team
from .context import PipelineContext


def load_player_squads_batch(
    ctx: PipelineContext,
    league_code: str,
    team_ids: set[int],
    season: int | None = None,
    require_complete: bool = False,
) -> None:
    squads_payload = {"league_code": league_code, "season": season, "response": []}
    if os.getenv("API_FOOTBALL_SKIP_PLAYER_SQUADS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"player_squads {league_code}: skipped (API_FOOTBALL_SKIP_PLAYER_SQUADS set — use on low-quota archive runs)"
        )
        return
    quota_cut = False
    for team_id in sorted(team_ids):
        if errors_quota._http_quota_exhausted:
            quota_cut = True
            break
        try:
            squad_rows = squads_response_for_team(
                ctx.headers,
                team_id,
                ctx.errors,
                error_context=f"player_squads {league_code} team_id={team_id}",
            )
            squads_payload["response"].append(
                {
                    "team_id": team_id,
                    "squad_payload": squad_rows,
                }
            )
        except Exception as e:
            ctx.errors.append(f"player_squads {league_code} team {team_id}: {e}")
    if not squads_payload["response"]:
        return
    if require_complete and quota_cut:
        # The catch-up snapshot must be COMPLETE per competition. stg_apif__squads selects the
        # latest snapshot per league_code, and a finished comp is skip-if-present (never re-fetched
        # whole), so persisting a partial row here would silently drop the unwritten teams from
        # staging. Discard the partial; the whole comp re-captures on the next run once quota frees
        # up. (In-season Phase 3b passes require_complete=False — it re-fetches whole every run, so
        # its partials are healed by the next complete snapshot.)
        ctx.errors.append(
            f"player_squads {league_code}: quota cut the catch-up mid-comp; partial discarded, retries next run"
        )
        return
    try:
        load_json_to_bq(
            ctx.client,
            raw_table("SQUADS"),
            squads_payload,
            as_json_payload=True,
            append=True,
            league_code=league_code,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"player_squads BQ {league_code}: {e}")


def select_squad_catchup_team_ids(
    finished_comps: list[tuple[str, int, set[int]]],
    active_team_ids: set[int],
    already_captured: set[tuple[int, int]],
) -> list[tuple[str, int, set[int]]]:
    """Pure policy: which finished-comp teams still need a squad snapshot.

    A squad is a team property, so capture each team once even if it appears in several
    finished competitions, and never if it is already covered:
    - skip teams active in any full-mode comp this run (captured in-season);
    - skip teams already stored for that season;
    - dedupe across comps (the first finished comp that owns a team wins).

    ``finished_comps`` is an ordered list of ``(league_code, season, team_ids)``. Returns the
    same shape with only the team_ids still to fetch, dropping comps that need nothing.
    Deterministic — no I/O.
    """
    seen: set[int] = set()
    plan: list[tuple[str, int, set[int]]] = []
    for league_code, season, team_ids in finished_comps:
        to_fetch: set[int] = set()
        for team_id in sorted(team_ids):
            if team_id in active_team_ids:
                continue
            if team_id in seen:
                continue
            if (team_id, season) in already_captured:
                continue
            to_fetch.add(team_id)
            seen.add(team_id)
        if to_fetch:
            plan.append((league_code, season, to_fetch))
    return plan


def captured_team_seasons(ctx: PipelineContext) -> set[tuple[int, int]]:
    """Read ``(team_id, season)`` pairs already stored in RAW_APIF_SQUADS (season-stamped rows).

    Lets the catch-up skip teams whose squad we already hold for that season. Returns an empty
    set if the table does not exist yet or the read fails (then the catch-up captures everything,
    which is the safe direction — a duplicate snapshot, never a silent miss).
    """
    # Fully-qualified read: raw_table() returns the bare name; a raw client query
    # needs project.dataset (the write path qualifies internally). Matches _fq in
    # loads/player_universe.py / coverage.py.
    table = f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('SQUADS')}"
    sql = f"""
        SELECT DISTINCT
            SAFE_CAST(JSON_VALUE(team_block, '$.team_id') AS INT64) AS team_id,
            SAFE_CAST(JSON_VALUE(payload, '$.season') AS INT64) AS season
        FROM `{table}`,
            UNNEST(JSON_QUERY_ARRAY(JSON_QUERY(payload, '$.response'), '$')) AS team_block
        WHERE JSON_VALUE(payload, '$.season') IS NOT NULL
    """
    pairs: set[tuple[int, int]] = set()
    try:
        for row in ctx.client.query(sql).result():
            if row.team_id is not None and row.season is not None:
                pairs.add((int(row.team_id), int(row.season)))
    except Exception as e:
        ctx.errors.append(f"player_squads catch-up: captured-seasons read failed: {e}")
    return pairs
