"""GET /players per team×season (batched) → RAW_*_PLAYERS."""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq, read_latest_payload_json
from ..settings import raw_league_table
from ..merge import merge_players_squad
from ..fixture_scheduling import players_response_for_team
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
        return
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
    valid_keys = {(int(tid), int(s)) for s in seasons_list for tid in team_ids}
    try:
        tbl = raw_league_table(league_code, "PLAYERS")
        prior = read_latest_payload_json(ctx.client, tbl)
        players_payload = merge_players_squad(
            prior,
            players_payload,
            league_code=league_code,
            valid_team_season=valid_keys,
        )
        load_json_to_bq(
            ctx.client,
            tbl,
            players_payload,
            as_json_payload=True,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"players BQ {league_code}: {e}")
