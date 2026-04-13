"""GET /players per team×season (batched) → RAW_*_PLAYERS."""

from __future__ import annotations

import os

from .. import errors_quota
from ..bq import load_json_to_bq
from ..config import raw_league_table
from ..fanout import players_response_for_team
from .context import PipelineContext


def load_squad_players_batch(
    ctx: PipelineContext,
    league_code: str,
    seasons_list: list[int],
    team_ids: set[int],
) -> None:
    players_payload = {"league_code": league_code, "response": []}
    if os.getenv("API_FOOTBALL_SKIP_PLAYERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"players {league_code}: skipped (API_FOOTBALL_SKIP_PLAYERS set — use on low-quota archive runs)"
        )
    else:
        for season in seasons_list:
            if errors_quota._http_quota_exhausted:
                break
            for team_id in sorted(team_ids):
                if errors_quota._http_quota_exhausted:
                    break
                try:
                    players_rows = players_response_for_team(
                        ctx.headers,
                        team_id,
                        season,
                        ctx.errors,
                        error_context=(
                            f"players {league_code} team_id={team_id} season={season}"
                        ),
                    )
                    players_payload["response"].append(
                        {
                            "team_id": team_id,
                            "season": season,
                            "players_payload": players_rows,
                        }
                    )
                except Exception as e:
                    ctx.errors.append(
                        f"players {league_code} team {team_id} season={season}: {e}"
                    )
    try:
        load_json_to_bq(
            ctx.client,
            raw_league_table(league_code, "PLAYERS"),
            players_payload,
            as_json_payload=True,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"players BQ {league_code}: {e}")
