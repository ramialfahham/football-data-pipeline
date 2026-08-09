"""Fetch /standings for all configured seasons → RAW_*_STANDINGS.

Each run fetches all seasons and writes a fresh complete snapshot row; the API returns
the full standings history on every call.

MERGE-ON-WRITE since #33 item 8b: the run appends its snapshot, then deletes this
league's older rows. The row covers ALL configured seasons, so nothing is lost —
staging already read only the latest row per league_code.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .. import quota as errors_quota
from ..bigquery import delete_superseded_league_rows, load_json_to_bq
from ..settings import raw_table
from ..quota import append_api_errors
from ..http_client import fetch_merged_paged, result_is_complete
from ..seasons import _merge_merged_paged
from .context import PipelineContext


def load_standings_if_enabled(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
    cov: dict[str, bool],
) -> None:
    if not cov.get("standings", True):
        ctx.errors.append(
            f"standings {league_code}: coverage metadata reported unsupported; attempting fetch anyway"
        )
    # #896: one row per league covering ALL configured seasons, read latest-per-league in
    # staging. Lose one season to a quota cut and the merged payload silently becomes a
    # shorter history that supersedes the full one. Complete or discard.
    complete = True
    standings_merged: dict | None = None
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            complete = False
            break
        try:
            st = fetch_merged_paged(
                "/standings",
                ctx.headers,
                {"league": league_id, "season": season},
                paginate=False,
            )
            # Before the next fetch: the quota flag latches for the rest of the run.
            if not result_is_complete(st):
                complete = False
            append_api_errors(st, f"standings {league_code} season={season}", ctx.errors)
            standings_merged = _merge_merged_paged(standings_merged, st)
        except Exception as e:
            complete = False
            ctx.errors.append(f"standings {league_code} season={season}: {e}")
    if standings_merged is None:
        ctx.errors.append(f"standings {league_code}: no payload fetched for configured seasons")
        return
    if not complete:
        ctx.errors.append(
            f"standings {league_code}: INCOMPLETE fetch — partial snapshot DISCARDED, prior "
            f"snapshot kept (#896); retries next run"
        )
        return
    try:
        ts = datetime.now(timezone.utc)
        load_json_to_bq(
            ctx.client,
            raw_table("STANDINGS"),
            standings_merged,
            as_json_payload=True,
            append=True,
            league_code=league_code,
            ingested_at=ts.isoformat(),
        )
        # #33 item 8b — see loads/transfers.py for why this is safe and why it runs
        # only past the completeness guard above.
        delete_superseded_league_rows(
            ctx.client, raw_table("STANDINGS"), league_code, ts
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"standings BQ {league_code}: {e}")
