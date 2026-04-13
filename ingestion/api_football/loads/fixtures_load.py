"""Merged /fixtures across seasons → RAW_*_FIXTURES_NEXT + id sets for downstream."""

from __future__ import annotations

import os

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..config import _env_int, raw_league_table
from ..errors_quota import append_api_errors
from ..http_client import fetch_merged_paged
from ..payload_merge import merge_fixtures_envelope
from ..seasons import _merge_merged_paged, fixtures_query_params
from .context import PipelineContext


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
    fixtures_merged: dict | None = None
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            break
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
    fx_tbl = raw_league_table(league_code, "FIXTURES_NEXT")
    prior_fx = read_latest_payload_json(ctx.client, fx_tbl)
    fixtures_merged = merge_fixtures_envelope(prior_fx, fixtures_merged)
    load_json_to_bq(
        ctx.client,
        fx_tbl,
        fixtures_merged,
        as_json_payload=True,
    )
    ctx.add_loaded(1)

    team_ids, fixture_ids = _fixture_team_ids_from_response(fixtures_merged.get("response", []))
    return fixtures_merged, team_ids, fixture_ids
