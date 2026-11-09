"""Fetch /players per team and season (batched) and append one row per fetch to RAW_APIF_PLAYERS.

Raw is append-only: a re-fetched key accumulates rows, and base dedups with latest-ingest-wins.
Only a complete fetch is written, because a written row marks the (team, season) as captured.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_payload_rows_to_bq
from ..settings import GCP_PROJECT_ID, DATASET_ID, raw_table
from ..fixture_scheduling import players_response_for_team
from .context import PipelineContext


def captured_player_team_seasons(ctx: PipelineContext) -> set[tuple[int, int]]:
    """Return the ``(team_id, season)`` pairs already in RAW_APIF_PLAYERS; empty on a failed read.

    An empty set means everything is fetched again: a duplicate download, never a silent miss."""
    table = f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('PLAYERS')}"
    sql = f"""
        SELECT DISTINCT
            SAFE_CAST(JSON_VALUE(team_block, '$.team_id') AS INT64) AS team_id,
            SAFE_CAST(JSON_VALUE(team_block, '$.season') AS INT64) AS season
        FROM `{table}`,
            UNNEST(JSON_QUERY_ARRAY(JSON_QUERY(payload, '$.response'), '$')) AS team_block
        WHERE JSON_VALUE(team_block, '$.season') IS NOT NULL
    """
    pairs: set[tuple[int, int]] = set()
    try:
        for row in ctx.client.query(sql).result():
            if row.team_id is not None and row.season is not None:
                pairs.add((int(row.team_id), int(row.season)))
    except Exception as e:
        ctx.errors.append(f"players: captured-seasons read failed: {e}")
    return pairs


def plan_player_team_season_fetch(
    seasons_list: list[int],
    team_ids: set[int],
    reference_season: int,
    already_captured: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """The reference season is always re-fetched, earlier seasons only when not already held."""
    plan: list[tuple[int, int]] = []
    for season in seasons_list:
        for team_id in sorted(team_ids):
            if season >= reference_season or (team_id, season) not in already_captured:
                plan.append((season, team_id))
    return plan


def load_squad_players_batch(
    ctx: PipelineContext,
    league_code: str,
    seasons_list: list[int],
    team_ids: set[int],
    reference_season: int | None = None,
    already_captured: set[tuple[int, int]] | None = None,
) -> None:
    """Fetch and store the /players roster per (team, season) for one competition.

    `already_captured` is the run-level set read once by the caller; this function adds every
    key it writes, so teams shared between competitions are not re-fetched. None reads it here.
    """
    if os.getenv("API_FOOTBALL_SKIP_PLAYERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"players {league_code}: skipped (API_FOOTBALL_SKIP_PLAYERS set — use on low-quota archive runs)"
        )
        return

    # Finished seasons already in RAW_APIF_PLAYERS are immutable and never re-requested.
    ref = (
        reference_season
        if reference_season is not None
        else (max(seasons_list) if seasons_list else 0)
    )
    if already_captured is None:
        already_captured = captured_player_team_seasons(ctx)
    fetch_keys = plan_player_team_season_fetch(seasons_list, team_ids, ref, already_captured)
    total = len(seasons_list) * len(team_ids)
    print(
        f"[api-football] league={league_code} phase=squad /players "
        f"to_fetch={len(fetch_keys)} skipped_cached={total - len(fetch_keys)}",
        flush=True,
    )

    rows: list[dict] = []
    written_keys: list[str] = []
    incomplete_keys: list[str] = []
    quota_cut = False
    for season, team_id in fetch_keys:
        if errors_quota._http_quota_exhausted:
            quota_cut = True
            break
        try:
            players_rows, complete = players_response_for_team(
                ctx.headers,
                team_id,
                season,
                ctx.errors,
                error_context=(
                    f"players {league_code} team_id={team_id} season={season}"
                ),
            )
            # A written row marks the (team, season) captured, so a historical season would never
            # be re-fetched and a transient failure would become a permanent hole.
            if not complete:
                incomplete_keys.append(f"{team_id}-{season}")
                continue
            rows.append(
                {
                    "league_code": league_code,
                    "response": [
                        {
                            "team_id": team_id,
                            "season": season,
                            "players_payload": players_rows,
                        }
                    ],
                }
            )
            written_keys.append(f"{team_id}-{season}")
        except Exception as e:
            ctx.errors.append(
                f"players {league_code} team {team_id} season={season}: {e}"
            )

    if rows:
        try:
            # Append only: base assembles current-per-entity, so an extra row per key merges there.
            load_json_payload_rows_to_bq(
                ctx.client,
                raw_table("PLAYERS"),
                rows,
                league_code=league_code,
                append=True,
            )
            ctx.add_loaded(1)
            # Only after a successful write: on failure the rows are not stored, so not captured.
            for key in written_keys:
                team_str, _, season_str = key.partition("-")
                already_captured.add((int(team_str), int(season_str)))
        except Exception as e:
            ctx.errors.append(f"players BQ {league_code}: {e}")

    if incomplete_keys:
        ctx.errors.append(
            f"players {league_code}: {len(incomplete_keys)} team-season(s) SKIPPED on an incomplete "
            f"fetch and kept their prior rows: {', '.join(incomplete_keys[:10])}"
            + (" ..." if len(incomplete_keys) > 10 else "")
        )

    if quota_cut:
        ctx.errors.append(
            f"players {league_code}: PARTIAL — quota exhausted mid-fetch; "
            f"{len(written_keys)} team-season(s) refreshed, the remainder keep their prior rows"
        )
