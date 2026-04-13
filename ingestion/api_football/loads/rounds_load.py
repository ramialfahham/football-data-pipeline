"""GET /fixtures/rounds (multi-season merge) → RAW_*_ROUNDS."""

from __future__ import annotations

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..http_client import fetch_json
from ..payload_merge import merge_rounds_season_blocks
from .context import PipelineContext


def load_rounds_merged(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
) -> None:
    rnd_tbl = raw_league_table(league_code, "ROUNDS")
    rounds_merged = read_latest_payload_json(ctx.client, rnd_tbl)
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            break
        try:
            rounds_pl = fetch_json(
                "/fixtures/rounds",
                ctx.headers,
                params={"league": league_id, "season": season},
            )
            append_api_errors(
                rounds_pl, f"fixtures/rounds {league_code} season={season}", ctx.errors
            )
            rounds_merged = merge_rounds_season_blocks(rounds_merged, season, rounds_pl)
        except Exception as e:
            ctx.errors.append(f"fixtures/rounds {league_code} season={season}: {e}")
    if rounds_merged is None:
        return
    try:
        load_json_to_bq(
            ctx.client,
            rnd_tbl,
            rounds_merged,
            as_json_payload=True,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"fixtures/rounds BQ {league_code}: {e}")
