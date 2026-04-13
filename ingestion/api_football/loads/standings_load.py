"""GET /standings (multi-season merge) → RAW_*_STANDINGS."""

from __future__ import annotations

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..http_client import fetch_merged_paged
from ..seasons import _merge_merged_paged
from .context import PipelineContext


def load_standings_if_enabled(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
    cov: dict[str, bool],
) -> None:
    if not cov["standings"]:
        return
    standings_merged: dict | None = None
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            break
        try:
            st = fetch_merged_paged(
                "/standings",
                ctx.headers,
                {"league": league_id, "season": season},
                paginate=False,
            )
            append_api_errors(st, f"standings {league_code} season={season}", ctx.errors)
            standings_merged = _merge_merged_paged(standings_merged, st)
        except Exception as e:
            ctx.errors.append(f"standings {league_code} season={season}: {e}")
    if standings_merged is None:
        return
    try:
        st_tbl = raw_league_table(league_code, "STANDINGS")
        prior = read_latest_payload_json(ctx.client, st_tbl)
        standings_merged = merge_standings_envelope(prior, standings_merged)
        load_json_to_bq(
            ctx.client,
            st_tbl,
            standings_merged,
            as_json_payload=True,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"standings BQ {league_code}: {e}")
