"""GET /leagues catalog → RAW_*_LEAGUES + season list + coverage flags."""

from __future__ import annotations

from ..settings import raw_league_table
from ..quota import append_api_errors
from ..fixture_scheduling import _coverage_for_season
from ..http_client import fetch_json
from ..bigquery import load_json_to_bq
from ..seasons import _seasons_for_ingestion
from .context import PipelineContext


def fetch_catalog_persist_and_plan(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    current_season: int | None = None,
    history_seasons: int | None = None,
    season_type: str = "split_year",
    *,
    poll_mode: bool = False,
) -> tuple[list[int], int, dict[str, bool]]:
    """
    Load league metadata to BigQuery, derive seasons to ingest, print coverage summary.

    Returns ``(seasons_list, reference_season, coverage_flags)``.
    """
    league_catalog = fetch_json("/leagues", ctx.headers, params={"id": league_id})
    append_api_errors(league_catalog, f"leagues/catalog {league_code}", ctx.errors)
    # Skip the BigQuery write when the API returned no league rows (rate limit,
    # auth error, transient outage). load_json_to_bq uses WRITE_TRUNCATE; an
    # empty payload would wipe valid leagues data and break the dim_league /
    # dim_competition_season relationship tests downstream.
    if league_catalog.get("response"):
        load_json_to_bq(
            ctx.client,
            raw_league_table(league_code, "LEAGUES"),
            league_catalog,
            as_json_payload=True,
        )
        ctx.add_loaded(1)
    else:
        ctx.errors.append(
            f"leagues/catalog {league_code}: API returned no response data; "
            "skipping BigQuery write to preserve existing data"
        )

    seasons_list = _seasons_for_ingestion(
        league_catalog,
        league_id,
        ctx.headers,
        ctx.errors,
        current_season=current_season,
        history_seasons=history_seasons,
        season_type=season_type,
    )
    reference_season = max(seasons_list)
    if poll_mode:
        seasons_list = [reference_season]
    cov = _coverage_for_season(league_catalog, reference_season)
    print(
        f"[api-football] league={league_code} seasons_to_ingest={seasons_list} "
        f"coverage_ref_season={reference_season}"
        f"{' poll_mode=1' if poll_mode else ''}",
        flush=True,
    )
    return seasons_list, reference_season, cov
