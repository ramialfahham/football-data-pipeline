"""Player top lists (/players/top*) → RAW_*_TOP* tables."""

from __future__ import annotations

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..http_client import fetch_merged_paged
from ..payload_merge import merge_top_list_envelope
from ..seasons import _merge_merged_paged
from .context import PipelineContext

TOP_SLUG_TO_TABLE = {
    "topscorers": "TOPSCORERS",
    "topassists": "TOPASSISTS",
    "topyellowcards": "TOPYELLOWCARDS",
    "topredcards": "TOPREDCARDS",
}


def load_top_lists(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
) -> None:
    tops_accum: dict[str, dict | None] = {slug: None for slug in TOP_SLUG_TO_TABLE}
    for slug, tbl in TOP_SLUG_TO_TABLE.items():
        for season in seasons_list:
            if errors_quota._http_quota_exhausted:
                break
            try:
                pl = fetch_merged_paged(
                    f"/players/{slug}",
                    ctx.headers,
                    {"league": league_id, "season": season},
                    paginate=False,
                )
                append_api_errors(
                    pl, f"players/{slug} {league_code} season={season}", ctx.errors
                )
                tops_accum[slug] = _merge_merged_paged(tops_accum[slug], pl)
            except Exception as e:
                ctx.errors.append(f"players/{slug} {league_code} season={season}: {e}")
        merged_top = tops_accum.get(slug)
        if merged_top is None:
            continue
        try:
            top_tbl = raw_league_table(league_code, tbl)
            prior = read_latest_payload_json(ctx.client, top_tbl)
            merged_top = merge_top_list_envelope(prior, merged_top)
            load_json_to_bq(
                ctx.client,
                top_tbl,
                merged_top,
                as_json_payload=True,
            )
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"players/{slug} BQ {league_code}: {e}")
