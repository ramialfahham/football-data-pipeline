"""Fetch /fixtures for all configured seasons → RAW_*_FIXTURES_NEXT + id sets for downstream.

Each run writes a COMPLETE snapshot as a new appended row, so the latest row alone is
the full picture (staging reads only the latest partition, and the full-refresh
fct_fixture rebuilds from it). Completeness is held two ways: a full run fetches every
configured season (reusing finished ones from cache, issue #283); a poll/idle run fetches
only the current season and CARRIES FORWARD the prior snapshot's other seasons (see
fetch_merge_and_persist_fixtures). Finished historical seasons never change (#283), so the
reused / carried rows stay current.

Historical seasons whose fixtures are all in a terminal state are skipped on
subsequent runs — the cached BQ payload is reused instead of calling the API
again, since those matches can never change (issue #283).

Caveats this implements around:
- **Current season is always re-fetched** — only seasons strictly older than the
  newest configured season can be skipped, so in-progress matches stay fresh.
- **Full-season fixture mode only** — the skip assumes the cached row is a complete
  season snapshot. It is gated on `API_FOOTBALL_FIXTURES_MODE` being a full-season
  mode (the default); under `from_to`/`next` the cache is only a window and is
  never treated as complete.
- **Conservative terminal set** — only statuses that are genuinely final count.
  PST (postponed) and ABD (abandoned) are excluded because they can later be
  rescheduled/replayed, which would silently freeze a season that still changes.
  A season holding any such fixture keeps re-fetching (slower, but correct).
- **Late provider corrections to completed *historical* seasons are not picked up**
  once skipped (tracked separately in the follow-up enhancement issue). The most
  recently completed season is covered for as long as it remains the current season.
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

# Fixture status codes that mean the match outcome is final and the row will never change.
# Deliberately excludes PST (postponed) and ABD (abandoned): both can later be
# rescheduled/replayed, so a season containing one must keep re-fetching. CANC/AWD/WO
# are administratively final (cancelled / awarded / walkover) and do not reopen.
_TERMINAL_STATUSES = frozenset({"FT", "AET", "PEN", "CANC", "AWD", "WO"})

# Fixture modes that fetch a competition's whole-season calendar (see fixtures_query_params).
# Only under these is the cached snapshot a complete season we can trust for skip detection.
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
    """True when every fixture for `season` in the cached payload has a terminal status.

    Returns False for an empty/absent season so a cold or partial cache always
    re-fetches rather than freezing a gap.
    """
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
    # Only consult the cache for skip detection when we fetch whole-season calendars;
    # under from_to/next the cached row is a window, not a complete season.
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
        # One line per season (avoids Windows/Cursor terminals interleaving two prints).
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
        # Do NOT append a snapshot from an empty fresh fetch. If the current season could not be
        # fetched (e.g. quota exhausted before it was reached), writing now would either blank the
        # league (an empty latest row) or — via the carry-forward below — re-stamp the prior
        # snapshot with today's timestamp, masking a failed run as a fresh complete one. Leave the
        # prior complete snapshot as "latest"; the error above flags the gap. (Review Finding 2.)
        return fixtures_merged, set(), set()

    # team_ids / fixture_ids come from the FRESHLY FETCHED seasons only — i.e. before the
    # completeness carry-forward below. A poll/idle run fetches only the latest season, and the
    # squad catch-up (run_poll_phases -> select_squad_catchup_team_ids) is keyed on that latest
    # season; deriving team_ids here keeps it latest-season-scoped and never re-introduces
    # historical-only teams that the carry-forward adds back to the written snapshot.
    team_ids, fixture_ids = _fixture_team_ids_from_response(fixtures_merged.get("response", []))

    # Completeness invariant (data_contract.md "Append-only writes"): every appended snapshot must
    # carry the FULL history, so the latest row alone is the complete picture — the full-refresh
    # fct_fixture rebuilds from it and would otherwise silently drop history. A poll/idle run only
    # fetches the current season (catalog.fetch_catalog_persist_and_plan collapses seasons_list to
    # keep team_ids latest-season-scoped), so carry forward every season the previous snapshot held
    # that this run did not refetch. Finished historical seasons never change (issue #283), so the
    # carried rows are current. Full mode is a no-op here: its season list already covers everything
    # in the prior snapshot, so nothing is carried.
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

    # Append this run's snapshot. It is kept COMPLETE by the carry-forward above (current season
    # freshly fetched + all prior seasons reused from the latest snapshot), so staging — which reads
    # only the latest partition — always sees full history.
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
