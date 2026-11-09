"""Fetch /standings for all configured seasons into RAW_*_STANDINGS.

Each run appends a complete snapshot and deletes nothing; staging reads the newest per league.
"""

from __future__ import annotations

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
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
    # The row covers all configured seasons and staging reads latest-per-league, so a partial
    # snapshot must be discarded rather than written.
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
        load_json_to_bq(
            ctx.client,
            raw_table("STANDINGS"),
            standings_merged,
            as_json_payload=True,
            append=True,
            league_code=league_code,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"standings BQ {league_code}: {e}")
