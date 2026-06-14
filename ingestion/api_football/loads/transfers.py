"""Fetch /transfers per team (batched) → RAW_APIF_TRANSFERS.

Each run fetches the full transfer history for all teams and appends a fresh
snapshot row. Transfers are not season-scoped — one /transfers?team= call returns
all of a team's players' moves. Fetching by team returns each move twice (once per
involved team); the base model dedups. No cross-run merge with prior BQ data.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..fixture_scheduling import transfers_response_for_team
from .context import PipelineContext


def load_transfers_batch(
    ctx: PipelineContext,
    league_code: str,
    team_ids: set[int],
) -> None:
    transfers_payload = {"league_code": league_code, "response": []}
    if os.getenv("API_FOOTBALL_SKIP_TRANSFERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"transfers {league_code}: skipped (API_FOOTBALL_SKIP_TRANSFERS set — use on low-quota archive runs)"
        )
        return
    for team_id in sorted(team_ids):
        if errors_quota._http_quota_exhausted:
            break
        try:
            transfers_rows = transfers_response_for_team(
                ctx.headers,
                team_id,
                ctx.errors,
                error_context=f"transfers {league_code} team_id={team_id}",
            )
            transfers_payload["response"].append(
                {
                    "team_id": team_id,
                    "transfers_payload": transfers_rows,
                }
            )
        except Exception as e:
            ctx.errors.append(f"transfers {league_code} team {team_id}: {e}")
    try:
        load_json_to_bq(
            ctx.client,
            raw_table("TRANSFERS"),
            transfers_payload,
            as_json_payload=True,
            append=True,
            league_code=league_code,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"transfers BQ {league_code}: {e}")
