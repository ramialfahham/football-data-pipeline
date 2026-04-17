"""Orchestrates API-Football → BigQuery raw loads (D1 MVP)."""

from __future__ import annotations

import os

from google.cloud import bigquery

from .bq import ensure_api_football_dataset
from .completeness import (
    completeness_summary_line,
    fail_on_incomplete,
    run_ingest_completeness_checks,
)
from .ingestion_lock import (
    acquire_ingest_lock,
    ensure_ingest_lock_table,
    new_run_id,
    release_ingest_lock,
)
from .config import (
    DATASET_ID,
    GCP_PROJECT_ID,
    LEAGUES,
    V1_SEASON_WINDOW_YEARS,
    _apply_ingest_profile_defaults,
    _env_truthy,
    _ingest_profile_name,
    effective_season_max,
    effective_season_min,
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


def _load_api_football(request):
    client = bigquery.Client(project=GCP_PROJECT_ID)
    ensure_api_football_dataset(client)
    ensure_ingest_lock_table(client)
    run_id = new_run_id()
    lock_acquired = False
    headers = get_headers()
    ctx = PipelineContext(client=client, headers=headers)

    try:
        if not acquire_ingest_lock(client, run_id):
            return (
                "Another api-football ingestion holds the BigQuery lease "
                f"(table {GCP_PROJECT_ID}.{DATASET_ID}.RAW_APIF_INGEST_LOCK). "
                "Wait for lease_until to pass, or set API_FOOTBALL_SKIP_INGEST_LOCK=1 for local-only use.",
                409,
            )
        lock_acquired = True

        reset_http_quota_exhausted()
        _apply_ingest_profile_defaults()
        _bind_quota_error_sink(ctx.errors)
        _lo = effective_season_min()
        _hi = effective_season_max()
        _raw = os.getenv("API_FOOTBALL_SEASON", "").strip() or "(unset -> auto)"
        _seasons_csv = os.getenv("API_FOOTBALL_SEASONS", "").strip() or "(unset)"
        _all_s = _env_truthy("API_FOOTBALL_ALL_SEASONS")
        _fx_mode = os.getenv("API_FOOTBALL_FIXTURES_MODE", "season").strip() or "season"
        _fan_pri = os.getenv("API_FOOTBALL_FANOUT_PRIORITY", "upcoming").strip() or "upcoming"
        print(
            f"[api-football] profile={_ingest_profile_name()!r} "
            f"inferred_single_season={season_year()} API_FOOTBALL_SEASON={_raw!r} "
            f"API_FOOTBALL_SEASONS={_seasons_csv!r} API_FOOTBALL_ALL_SEASONS={_all_s} "
            f"v1_seasons_last_{V1_SEASON_WINDOW_YEARS}={_lo}-{_hi} "
            f"fixtures_mode={_fx_mode!r} fanout_priority={_fan_pri!r} run_id={run_id}",
            flush=True,
        )

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

        report = run_ingest_completeness_checks(client)
        print(completeness_summary_line(report), flush=True)
        match_ok = report.get(
            "match_level_tables_cover_all_fixtures",
            report.get("all_fanout_complete", True),
        )
        if fail_on_incomplete() and not report.get("skipped") and not match_ok:
            msg += (
                " Per-match raw tables (lineups, events, statistics, "
                "fixture players, predictions) do not yet cover every fixture id "
                "in the merged fixtures list."
            )
            return msg, 503

        return msg, 200
    except Exception as e:
        return f"Pipeline failed: {e}", 500
    finally:
        if lock_acquired:
            release_ingest_lock(client, run_id)
        _bind_quota_error_sink(None)
