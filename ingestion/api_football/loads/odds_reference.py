"""Global reference tables: /odds/bookmakers, /odds/bets."""

from __future__ import annotations

import os

from ..bq import load_json_to_bq
from ..errors_quota import append_api_errors
from ..http_client import fetch_merged_paged
from .context import PipelineContext


def load_odds_reference_tables(ctx: PipelineContext) -> None:
    if os.getenv("API_FOOTBALL_SKIP_ODDS_REFERENCE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return
    try:
        ob = fetch_merged_paged("/odds/bookmakers", ctx.headers, {}, paginate=False)
        append_api_errors(ob, "odds/bookmakers", ctx.errors)
        load_json_to_bq(ctx.client, "RAW_APIF_ODDS_BOOKMAKERS", ob, as_json_payload=True)
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"odds/bookmakers: {e}")
    try:
        bet_tbl = fetch_merged_paged("/odds/bets", ctx.headers, {}, paginate=False)
        append_api_errors(bet_tbl, "odds/bets", ctx.errors)
        load_json_to_bq(ctx.client, "RAW_APIF_ODDS_BETS", bet_tbl, as_json_payload=True)
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"odds/bets: {e}")
