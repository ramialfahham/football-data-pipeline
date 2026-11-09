"""Fetch /fixtures for all configured seasons into RAW_*_FIXTURES_NEXT and return the id sets.

Each appended snapshot must be complete, because staging reads only the latest partition.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq, read_latest_payload_json
from ..settings import _env_int, raw_table
from ..quota import append_api_errors
from ..http_client import fetch_merged_paged
from ..seasons import _merge_merged_paged, fixtures_query_params
from .context import PipelineContext

# Excludes PST (postponed) and ABD (abandoned): both can be rescheduled or replayed, so a season
# containing one must keep re-fetching.
_TERMINAL_STATUSES = frozenset({"FT", "AET", "PEN", "CANC", "AWD", "WO"})

# Only under these modes is the cached snapshot a complete season that skip detection can trust.
_FULL_SEASON_FIXTURE_MODES = frozenset({"season", "league", "full", "all"})


def _is_full_season_fixture_mode() -> bool:
    mode = os.getenv("API_FOOTBALL_FIXTURES_MODE", "season").strip().lower()
    return mode in _FULL_SEASON_FIXTURE_MODES


def _fixtures_for_season(fixtures_response: list, season: int) -> list:
    return [f for f in fixtures_response if f.get("league", {}).get("season") == season]


def _seasons_in_response(fixtures_response: list) -> set:
    """Distinct API season years present in a ``/fixtures`` response list."""
    seasons: set = set()
    for item in fixtures_response or []:
        season = (item.get("league") or {}).get("season")
        if season is not None:
            seasons.add(season)
    return seasons


def _season_complete_in_cache(cached_response: list, season: int) -> bool:
    """True when every cached fixture for `season` is terminal; False if none, so gaps re-fetch."""
    season_fixtures = _fixtures_for_season(cached_response, season)
    if not season_fixtures:
        return False
    return all(
        f.get("fixture", {}).get("status", {}).get("short") in _TERMINAL_STATUSES
        for f in season_fixtures
    )


def _fixture_team_ids_from_response(fixtures_response: list) -> tuple[set[int], set[int]]:
    team_ids: set[int] = set()
    fixture_ids: set[int] = set()
    for item in fixtures_response or []:
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        if fixture.get("id"):
            fixture_ids.add(int(fixture["id"]))
        if home.get("id"):
            team_ids.add(int(home["id"]))
        if away.get("id"):
            team_ids.add(int(away["id"]))
    return team_ids, fixture_ids


def fetch_merge_and_persist_fixtures(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
) -> tuple[dict, set[int], set[int]]:
    current_season = max(seasons_list)
    # Under from_to/next the cached row is a window, not a complete season.
    skip_eligible = _is_full_season_fixture_mode()
    cached_response: list = []
    if skip_eligible:
        cached_payload = read_latest_payload_json(
            ctx.client, raw_table("FIXTURES_NEXT"), league_code=league_code
        )
        cached_response = (cached_payload or {}).get("response") or []

    fixtures_merged: dict | None = None
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            break

        if (
            skip_eligible
            and season < current_season
            and _season_complete_in_cache(cached_response, season)
        ):
            season_fixtures = _fixtures_for_season(cached_response, season)
            cached_part: dict = {
                "response": season_fixtures,
                "errors": [],
                "results": len(season_fixtures),
                "paging": {"current": 1, "total": 1},
            }
            fixtures_merged = _merge_merged_paged(fixtures_merged, cached_part)
            n_part = len(season_fixtures)
            n_tot = len(fixtures_merged.get("response") or [])
            print(
                f"[api-football] fixtures {league_code} season={season} "
                f"response_rows_this_season={n_part} cumulative_rows={n_tot} (cached — season complete)",
                flush=True,
            )
            continue

        fx_params = fixtures_query_params(league_id, season)
        use_page = os.getenv("API_FOOTBALL_FIXTURES_USE_PAGE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        fixtures_paginate = use_page and "from" not in fx_params and "next" not in fx_params
        fixtures_part = fetch_merged_paged(
            "/fixtures",
            ctx.headers,
            fx_params,
            paginate=fixtures_paginate,
            max_pages=_env_int("API_FOOTBALL_FIXTURES_MAX_PAGE", 50) if fixtures_paginate else None,
        )
        append_api_errors(
            fixtures_part, f"fixtures {league_code} season={season}", ctx.errors
        )
        fixtures_merged = _merge_merged_paged(fixtures_merged, fixtures_part)
        n_part = len(fixtures_part.get("response") or [])
        n_tot = len(fixtures_merged.get("response") or [])
        # One print per season so terminals do not interleave two lines.
        print(
            f"[api-football] fixtures {league_code} season={season} "
            f"response_rows_this_season={n_part} cumulative_rows={n_tot}",
            flush=True,
        )

    if fixtures_merged is None:
        fixtures_merged = {
            "response": [],
            "errors": [],
            "results": 0,
            "paging": {"current": 1, "total": 1},
        }
    append_api_errors(fixtures_merged, f"fixtures {league_code}", ctx.errors)
    n_fx = len(fixtures_merged.get("response") or [])
    if n_fx == 0:
        params = fixtures_merged.get("parameters")
        ctx.errors.append(
            f"fixtures {league_code}: empty response for seasons={seasons_list!r} "
            f"parameters={params!r} — check API errors above, API_FOOTBALL_FIXTURES_MODE "
            f"(from_to needs sensible dates), or quota; then re-run ingest."
        )
        # An empty fetch writes nothing: it would blank the league or, via the carry-forward below,
        # re-stamp the prior snapshot as fresh and mask a failed run.
        return fixtures_merged, set(), set()

    # Derived before the carry-forward so team_ids stay scoped to the freshly fetched seasons,
    # which the squad catch-up relies on.
    team_ids, fixture_ids = _fixture_team_ids_from_response(fixtures_merged.get("response", []))

    # Every appended snapshot must carry the full history because fct_fixture rebuilds from the
    # latest row alone; a poll run fetches only the current season, so carry forward the rest.
    if skip_eligible and cached_response:
        fetched_seasons = _seasons_in_response(fixtures_merged.get("response") or [])
        carried = [
            f
            for f in cached_response
            if ((f.get("league") or {}).get("season")) not in fetched_seasons
        ]
        if carried:
            fixtures_merged = _merge_merged_paged(
                fixtures_merged,
                {
                    "response": carried,
                    "errors": [],
                    "results": len(carried),
                    "paging": {"current": 1, "total": 1},
                },
            )
            print(
                f"[api-football] fixtures {league_code} carried_forward_rows={len(carried)} "
                f"cumulative_rows={len(fixtures_merged.get('response') or [])} "
                "(completeness: prior-snapshot seasons not refetched this run)",
                flush=True,
            )

    fx_tbl = raw_table("FIXTURES_NEXT")
    load_json_to_bq(
        ctx.client,
        fx_tbl,
        fixtures_merged,
        as_json_payload=True,
        append=True,
        league_code=league_code,
    )
    ctx.add_loaded(1)

    return fixtures_merged, team_ids, fixture_ids
