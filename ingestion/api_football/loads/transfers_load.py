"""GET /transfers per team (paginated merge) → RAW_*_TRANSFERS."""

from __future__ import annotations

import os

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..config import _env_int, raw_league_table
from ..errors_quota import append_api_errors, _flatten_api_errors
from ..http_client import fetch_merged_paged
from ..payload_merge import merge_transfers_envelope
from .context import PipelineContext


def load_transfers_if_enabled(
    ctx: PipelineContext,
    league_code: str,
    team_ids: set[int],
) -> None:
    if os.getenv("API_FOOTBALL_FETCH_TRANSFERS", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return
    try:
        use_page = os.getenv("API_FOOTBALL_TRANSFERS_USE_PAGE", "0").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        tr_pages = _env_int("API_FOOTBALL_TRANSFERS_MAX_PAGE", 3)
        merged_tr: list = []
        tr_errors: list[str] = []
        tr_meta: dict | None = None
        for tid in sorted(team_ids):
            if errors_quota._http_quota_exhausted:
                break
            tr_part = fetch_merged_paged(
                "/transfers",
                ctx.headers,
                {"team": tid},
                paginate=use_page,
                max_pages=tr_pages if use_page else None,
            )
            if tr_meta is None:
                tr_meta = {
                    k: v
                    for k, v in tr_part.items()
                    if k not in ("response", "errors", "results", "paging")
                }
            tr_errors.extend(_flatten_api_errors(tr_part.get("errors")))
            merged_tr.extend(tr_part.get("response") or [])
        tr = dict(tr_meta or {})
        tr["errors"] = tr_errors
        tr["response"] = merged_tr
        tr["results"] = len(merged_tr)
        tr["paging"] = {"current": 1, "total": 1}
        append_api_errors(tr, f"transfers {league_code}", ctx.errors)
        tr_tbl = raw_league_table(league_code, "TRANSFERS")
        prior = read_latest_payload_json(ctx.client, tr_tbl)
        tr = merge_transfers_envelope(prior, tr)
        load_json_to_bq(
            ctx.client,
            tr_tbl,
            tr,
            as_json_payload=True,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"transfers {league_code}: {e}")
