"""Fetch /transfers per team (batched) → RAW_APIF_TRANSFERS, appending one snapshot per run.

Raw is append-only and `stg_apif__transfers` selects the newest row per league_code.
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
    # With empty `team_ids` the loop never runs and an empty snapshot would be written as the
    # latest row, hiding the real transfer history downstream.
    if not team_ids:
        ctx.errors.append(
            f"transfers {league_code}: no team ids this run — SKIPPED, prior snapshot kept"
        )
        return
    transfers_payload = {"league_code": league_code, "response": []}
    if os.getenv("API_FOOTBALL_SKIP_TRANSFERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"transfers {league_code}: skipped (API_FOOTBALL_SKIP_TRANSFERS set — use on low-quota archive runs)"
        )
        return
    # The payload is one row per league and staging reads the latest, so a partial snapshot
    # must not be written.
    complete = True
    for team_id in sorted(team_ids):
        if errors_quota._http_quota_exhausted:
            complete = False
            break
        try:
            transfers_rows, team_complete = transfers_response_for_team(
                ctx.headers,
                team_id,
                ctx.errors,
                error_context=f"transfers {league_code} team_id={team_id}",
            )
            if not team_complete:
                complete = False
                continue
            transfers_payload["response"].append(
                {
                    "team_id": team_id,
                    "transfers_payload": transfers_rows,
                }
            )
        except Exception as e:
            complete = False
            ctx.errors.append(f"transfers {league_code} team {team_id}: {e}")
    if not complete:
        ctx.errors.append(
            f"transfers {league_code}: INCOMPLETE fetch — partial snapshot DISCARDED, prior "
            f"snapshot kept (#896); retries next run"
        )
        return
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
