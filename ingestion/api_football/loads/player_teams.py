"""Fetch /players/teams per player into RAW_APIF_PLAYER_TEAMS, one snapshot row per league."""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..fixture_scheduling import player_teams_response_for_player
from .context import PipelineContext
from .player_universe import players_needing


def load_player_teams_global(
    ctx: PipelineContext,
    universe: list[tuple[int, str]] | None,
) -> None:
    """`universe` is the run's shared `_query_universe()` result; it has no default so the shared
    read cannot be silently dropped.
    """
    if os.getenv("API_FOOTBALL_SKIP_PLAYER_TEAMS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            "player_teams: skipped (API_FOOTBALL_SKIP_PLAYER_TEAMS set — use on low-quota archive runs)"
        )
        return
    try:
        by_league = players_needing(ctx.client, "PLAYER_TEAMS", universe=universe)
    except Exception as e:
        ctx.errors.append(f"player_teams universe: {e}")
        return
    for league_code in sorted(by_league):
        if errors_quota._http_quota_exhausted:
            break
        teams_payload = {"league_code": league_code, "response": []}
        for player_id in by_league[league_code]:
            if errors_quota._http_quota_exhausted:
                break
            try:
                team_rows, complete = player_teams_response_for_player(
                    ctx.headers,
                    player_id,
                    ctx.errors,
                    error_context=f"player_teams {league_code} player_id={player_id}",
                )
                # `_existing_player_ids` keys on `$.player_id` presence, so storing an incomplete
                # career would retire the player permanently.
                if not complete:
                    ctx.errors.append(
                        f"player_teams {league_code} player {player_id}: INCOMPLETE fetch — "
                        f"player SKIPPED, not marked ingested; retries next run"
                    )
                    continue
                teams_payload["response"].append(
                    {
                        "player_id": player_id,
                        "teams_payload": team_rows,
                    }
                )
            except Exception as e:
                ctx.errors.append(f"player_teams {league_code} player {player_id}: {e}")
        if not teams_payload["response"]:
            continue
        try:
            load_json_to_bq(
                ctx.client,
                raw_table("PLAYER_TEAMS"),
                teams_payload,
                as_json_payload=True,
                append=True,
                league_code=league_code,
            )
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"player_teams BQ {league_code}: {e}")
