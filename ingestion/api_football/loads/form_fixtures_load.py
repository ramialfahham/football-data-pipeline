"""Fetch qualifier fixtures per supporting league → RAW_{league_code}_APIF_FORM_FIXTURES."""

from __future__ import annotations

from .. import errors_quota
from ..bq import load_json_to_bq
from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..http_client import fetch_json
from .context import PipelineContext


def load_form_fixtures(
    ctx: PipelineContext,
    league_code: str,
    supporting_leagues: tuple,
) -> None:
    """Fetch fixtures for each supporting league and store as one batched payload.

    Each entry in ``supporting_leagues`` must be a dict with ``id`` (int) and
    optionally ``season`` (int). Queries ``/fixtures?league={id}&season={year}``.
    """
    league_blocks: list[dict] = []

    for sl in supporting_leagues:
        if errors_quota._http_quota_exhausted:
            break
        league_id = sl["id"]
        season = sl.get("season")
        params: dict = {"league": league_id}
        if season is not None:
            params["season"] = season
        try:
            result = fetch_json("/fixtures", ctx.headers, params)
            append_api_errors(
                result,
                f"form_fixtures {league_code} league_id={league_id} season={season}",
                ctx.errors,
            )
            fixture_count = len(result.get("response") or [])
            print(
                f"[api-football] form_fixtures league={league_code} "
                f"league_id={league_id} season={season} fixtures={fixture_count}",
                flush=True,
            )
            league_blocks.append(
                {
                    "queried_league_id": league_id,
                    "queried_season": season,
                    "response": result.get("response") or [],
                }
            )
        except Exception as e:
            ctx.errors.append(
                f"form_fixtures {league_code} league_id={league_id} season={season}: {e}"
            )

    if not league_blocks:
        print(
            f"[api-football] form_fixtures league={league_code} no data fetched — skipping BQ write",
            flush=True,
        )
        return

    payload = {"league_code": league_code, "response": league_blocks}
    try:
        tbl = raw_league_table(league_code, "FORM_FIXTURES")
        load_json_to_bq(ctx.client, tbl, payload, as_json_payload=True)
        ctx.add_loaded(1)
        print(
            f"[api-football] form_fixtures league={league_code} "
            f"leagues={len(league_blocks)} written to {tbl}",
            flush=True,
        )
    except Exception as e:
        ctx.errors.append(f"form_fixtures BQ {league_code}: {e}")
