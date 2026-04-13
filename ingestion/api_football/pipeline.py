"""Orchestrates API-Football → BigQuery raw loads (D1 MVP)."""

from __future__ import annotations

import os

from google.cloud import bigquery

from .bq import ensure_api_football_dataset
from .config import (
    GCP_PROJECT_ID,
    LEAGUES,
    _apply_ingest_profile_defaults,
    _default_season_max,
    _default_season_min,
    _env_truthy,
    _ingest_profile_name,
    get_headers,
    season_year,
)
from .errors_quota import (
    _bind_quota_error_sink,
    _dedupe_errors_preserve_order,
    reset_http_quota_exhausted,
)
from .loads.context import PipelineContext
from .loads.league_pipeline import ingest_league
from .loads.odds_reference import load_odds_reference_tables


def _load_api_football(request):
    client = bigquery.Client(project=GCP_PROJECT_ID)
    ensure_api_football_dataset(client)
    headers = get_headers()
    ctx = PipelineContext(client=client, headers=headers)

    try:
        reset_http_quota_exhausted()
        _apply_ingest_profile_defaults()
        _bind_quota_error_sink(ctx.errors)
        _lo = _default_season_min()
        _hi = _default_season_max()
        _raw = os.getenv("API_FOOTBALL_SEASON", "").strip() or "(unset -> auto)"
        _seasons_csv = os.getenv("API_FOOTBALL_SEASONS", "").strip() or "(unset)"
        _all_s = _env_truthy("API_FOOTBALL_ALL_SEASONS")
        _fx_mode = os.getenv("API_FOOTBALL_FIXTURES_MODE", "season").strip() or "season"
        _fan_pri = os.getenv("API_FOOTBALL_FANOUT_PRIORITY", "upcoming").strip() or "upcoming"
        print(
            f"[api-football] profile={_ingest_profile_name()!r} "
            f"inferred_single_season={season_year()} API_FOOTBALL_SEASON={_raw!r} "
            f"API_FOOTBALL_SEASONS={_seasons_csv!r} API_FOOTBALL_ALL_SEASONS={_all_s} "
            f"season_band_when_unset={_lo}-{_hi} fixtures_mode={_fx_mode!r} "
            f"fanout_priority={_fan_pri!r}",
            flush=True,
        )

        print("[api-football] phase=odds_reference (bookmakers/bets)", flush=True)
        load_odds_reference_tables(ctx)
        for league_code, league_id in LEAGUES.items():
            ingest_league(ctx, league_code, league_id)

        msg = f"Loaded {ctx.tables_loaded} API-Football tables."
        if ctx.errors:
            uniq = _dedupe_errors_preserve_order(ctx.errors)
            shown = uniq[:40]
            tail = "; ".join(shown)
            if len(uniq) > 40:
                tail += f" ... (+{len(uniq) - 40} more distinct notes)"
            msg += f" Notes: {tail}"
        return msg, 200
    except Exception as e:
        return f"Pipeline failed: {e}", 500
    finally:
        _bind_quota_error_sink(None)
