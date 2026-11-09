"""Fetch /players/squads per team and append one snapshot row per league to RAW_APIF_SQUADS.

The snapshot is stamped with ``season`` because ``captured_team_seasons`` reads it back.
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
            squad_rows, complete = squads_response_for_team(
                ctx.headers,
                team_id,
                ctx.errors,
                error_context=f"player_squads {league_code} team_id={team_id}",
            )
            # `captured_team_seasons` reads `$.team_id` presence, so storing an incomplete squad
            # would mark the team done and no later run would re-fetch it.
            if not complete:
                ctx.errors.append(
                    f"player_squads {league_code} team {team_id}: INCOMPLETE fetch — team SKIPPED, "
                    f"not marked captured; retries next run"
                )
                continue
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
        # stg_apif__squads selects the latest snapshot per league_code and a finished comp is never
        # re-fetched whole, so a partial row would drop the unwritten teams from staging.
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
    """Return the ``finished_comps`` shape with only the team_ids still needing a squad snapshot.

    Skips teams active in a full-mode comp, teams already stored for that season, and teams
    already owned by an earlier finished comp.
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
    """Read ``(team_id, season)`` pairs already stored in RAW_APIF_SQUADS.

    Returns an empty set when the read fails, so the catch-up over-captures rather than misses.
    """
    # raw_table() returns the bare name, but a raw client query needs project.dataset.
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
