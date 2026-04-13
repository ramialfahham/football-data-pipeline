"""GET /leagues catalog → RAW_*_LEAGUES + season list + coverage flags."""

from __future__ import annotations

from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..fanout import _coverage_for_season
from ..http_client import fetch_json
from ..bq import load_json_to_bq
from ..seasons import _seasons_for_ingestion
from .context import PipelineContext


def fetch_catalog_persist_and_plan(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
) -> tuple[list[int], int, dict[str, bool]]:
    """
    Load league metadata to BigQuery, derive seasons to ingest, print coverage summary.

    Returns ``(seasons_list, reference_season, coverage_flags)``.
    """
    league_catalog = fetch_json("/leagues", ctx.headers, params={"id": league_id})
    append_api_errors(league_catalog, f"leagues/catalog {league_code}", ctx.errors)
    load_json_to_bq(
        ctx.client,
        raw_league_table(league_code, "LEAGUES"),
        league_catalog,
        as_json_payload=True,
    )
    ctx.add_loaded(1)

    seasons_list = _seasons_for_ingestion(league_catalog, league_id, ctx.headers, ctx.errors)
    reference_season = max(seasons_list)
    cov = _coverage_for_season(league_catalog, reference_season)
    print(
        f"[api-football] league={league_code} seasons_to_ingest={seasons_list} "
        f"coverage_ref_season={reference_season}",
        flush=True,
    )
    return seasons_list, reference_season, cov
