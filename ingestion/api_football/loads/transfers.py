"""Fetch /transfers per team (batched) → RAW_APIF_TRANSFERS.

Each run fetches the full transfer history for all teams and writes a fresh snapshot
row. Transfers are not season-scoped — one /transfers?team= call returns all of a
team's players' moves. Fetching by team returns each move twice (once per involved
team); the base model dedups.

MERGE-ON-WRITE since #33 item 8b: the run appends its snapshot, then deletes this
league's older rows. The row is the WHOLE league, so nothing is lost — staging already
read only the latest row per league_code.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from .. import quota as errors_quota
from ..bigquery import delete_superseded_league_rows, load_json_to_bq
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
    # #896: this payload is ONE row for the whole league, and staging reads the latest row per
    # league_code. So it is complete or it is worthless — there is no per-team key to withhold
    # the way squads.py can. Any team that could not be fetched cleanly makes the snapshot
    # partial, and a partial must not supersede the good one already stored.
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
        # Discard rather than supersede. Under today's append-only writes the stored snapshot
        # simply stays the latest; once #33 item 8b makes this table merge-on-write, writing
        # here would DELETE that stored snapshot, so this guard is what makes 8b safe.
        ctx.errors.append(
            f"transfers {league_code}: INCOMPLETE fetch — partial snapshot DISCARDED, prior "
            f"snapshot kept (#896); retries next run"
        )
        return
    try:
        ts = datetime.now(timezone.utc)
        load_json_to_bq(
            ctx.client,
            raw_table("TRANSFERS"),
            transfers_payload,
            as_json_payload=True,
            append=True,
            league_code=league_code,
            ingested_at=ts.isoformat(),
        )
        # #33 item 8b. Reachable only past the completeness guard above, so a partial
        # snapshot never deletes anything. Strictly BEFORE `ts` keeps the row just
        # written. If the delete raises, the append already stood and both rows remain —
        # staging still selects the newer one, so a failure costs the saving, never data.
        delete_superseded_league_rows(
            ctx.client, raw_table("TRANSFERS"), league_code, ts
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"transfers BQ {league_code}: {e}")
