"""GET /injuries (multi-season merge) → RAW_*_INJURIES."""

from __future__ import annotations

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..http_client import fetch_merged_paged
from ..payload_merge import merge_injuries_envelope
from ..seasons import _merge_merged_paged
from .context import PipelineContext


def load_injuries_if_enabled(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
    cov: dict[str, bool],
) -> None:
    if not cov["injuries"]:
        return
    injuries_merged: dict | None = None
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            break
        try:
            injuries_part = fetch_merged_paged(
                "/injuries",
                ctx.headers,
                {"league": league_id, "season": season},
                paginate=False,
            )
            append_api_errors(
                injuries_part,
                f"injuries {league_code} season={season}",
                ctx.errors,
            )
            injuries_merged = _merge_merged_paged(injuries_merged, injuries_part)
        except Exception as e:
            ctx.errors.append(f"injuries {league_code} season={season}: {e}")
    if injuries_merged is None:
        return
    try:
        inj_tbl = raw_league_table(league_code, "INJURIES")
        prior = read_latest_payload_json(ctx.client, inj_tbl)
        injuries_merged = merge_injuries_envelope(prior, injuries_merged)
        load_json_to_bq(
            ctx.client,
            inj_tbl,
            injuries_merged,
            as_json_payload=True,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"injuries BQ {league_code}: {e}")
