"""Fetch /fixtures/rounds for all configured seasons → RAW_*_ROUNDS.

Each run builds a fresh multi-season payload by calling the API once per season
and assembling the results in memory with merge_rounds_season_blocks. The assembled
payload is then appended as a new row — no cross-run merge with prior BQ data.
"""

from __future__ import annotations

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..quota import append_api_errors
from ..http_client import fetch_json
from ..merge import merge_rounds_season_blocks
from .context import PipelineContext


def load_rounds_merged(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
) -> None:
    rnd_tbl = raw_table("ROUNDS")
    # Start with None — build the payload fresh from this run's API calls.
    # merge_rounds_season_blocks accumulates seasons within this run only.
    rounds_merged = None
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
            append=True,
            league_code=league_code,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"fixtures/rounds BQ {league_code}: {e}")
