"""Fetch /players/squads per team (batched) → RAW_APIF_SQUADS.

The current squad of each team (id, name, age, number, position, photo) in one call per
team. Distinct from loads/squads.py, which pulls /players per team×season into
RAW_APIF_PLAYERS (season roster + stats); this is the cheaper present-day squad endpoint and
is the only one that carries the shirt number. Each run appends a fresh complete snapshot row
per league. No cross-run merge with prior BQ data.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..fixture_scheduling import squads_response_for_team
from .context import PipelineContext


def load_player_squads_batch(
    ctx: PipelineContext,
    league_code: str,
    team_ids: set[int],
) -> None:
    squads_payload = {"league_code": league_code, "response": []}
    if os.getenv("API_FOOTBALL_SKIP_PLAYER_SQUADS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"player_squads {league_code}: skipped (API_FOOTBALL_SKIP_PLAYER_SQUADS set — use on low-quota archive runs)"
        )
        return
    for team_id in sorted(team_ids):
        if errors_quota._http_quota_exhausted:
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
