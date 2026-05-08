"""Top-level orchestrator: reads the competition registry and runs ingestion for each active competition.

Entry point for the Cloud Function (and local runs via main.py). Acquires a BigQuery
ingest lock to prevent concurrent runs, then iterates over selected competitions from
the registry, calling ingest_league() for each. Results land in RAW_APIF_{LEAGUE_CODE}_*
tables in the raw BigQuery dataset.

To add a new competition: add it to docs/competition_registry.yml with status=active
(or in_progress with API_FOOTBALL_INCLUDE_IN_PROGRESS=1). No code changes required.
"""

from __future__ import annotations

import os

from google.cloud import bigquery

from .bigquery import ensure_api_football_dataset
from .completeness import (
    completeness_markdown_summary,
    completeness_summary_line,
    evaluate_completeness_outcome,
    run_ingest_completeness_checks,
    write_step_summary_if_configured,
)
from .ingestion_lock import (
    acquire_ingest_lock,
    ensure_ingest_lock_table,
    new_run_id,
    release_ingest_lock,
)
from .settings import (
    DATASET_ID,
    GCP_PROJECT_ID,
    V1_SEASON_WINDOW_YEARS,
    _apply_ingest_profile_defaults,
    _env_truthy,
    _ingest_profile_name,
    get_headers,
)
from .season_inference import (
    effective_season_max,
    effective_season_min,
    season_year,
)
from .registry import (
    include_in_progress_competitions,
    selected_competitions,
)
from .quota import (
    _bind_quota_error_sink,
    _dedupe_errors_preserve_order,
    reset_http_quota_exhausted,
)
from .loads.context import PipelineContext
from .loads.competition_runner import run_cheap_phases, run_squads_for_competition
from .loads.fanout import run_global_fanout_and_persist


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
            f"fixtures_mode={_fx_mode!r} fanout_priority={_fan_pri!r} "
            f"include_in_progress={include_in_progress_competitions()} run_id={run_id}",
            flush=True,
        )

        selected, skipped = selected_competitions()
        selected_log = ", ".join(
            f"{c.league_code}:{c.provider_league_id} ({c.status})" for c in selected
        )
        print(f"[api-football] selected_competitions={selected_log}", flush=True)
        for comp, reason in skipped:
            print(
                f"[api-football] skipped_competition league={comp.league_code} "
                f"provider_league_id={comp.provider_league_id} status={comp.status} reason={reason}",
                flush=True,
            )

        # Phase 1: cheap phases for all competitions (catalog, fixtures, standings, etc.)
        results = []
        for comp in selected:
            result = run_cheap_phases(
                ctx,
                comp.league_code,
                comp.provider_league_id,
                current_season=comp.current_season,
                history_seasons=comp.history_seasons,
            )
            if result is not None:
                results.append(result)

        # Phase 2: global completeness-driven fanout across all competitions
        if results:
            run_global_fanout_and_persist(ctx, results)

        # Phase 3: squad /players batch per competition
        for result in results:
            run_squads_for_competition(ctx, result)

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

        # Tiered outcome: hard-fail only when an `active` competition is
        # incomplete; in_progress competitions warn and stay green.
        outcome = evaluate_completeness_outcome(report)

        # Always render the markdown summary so the per-competition coverage
        # state is visible on every workflow run page.
        notes: list[str] = []
        notes.append(f"Loaded {ctx.tables_loaded} API-Football tables.")
        if outcome["in_progress_partial"]:
            partial_codes = ", ".join(
                f"{p['league_code']} ({p['total_missing']} missing)"
                for p in outcome["in_progress_partial"]
            )
            notes.append(
                f"in_progress backfill still in flight: {partial_codes}. "
                "Run is green; coverage will close over subsequent days."
            )
        if outcome["active_failures"]:
            for f in outcome["active_failures"]:
                eps = ", ".join(
                    f"{m['endpoint']} ({m['missing_count']}/{m['expected_count']})"
                    for m in f["missing_endpoints"]
                )
                notes.append(
                    f"ACTIVE competition incomplete: {f['league_code']} — {eps}"
                )
        markdown = completeness_markdown_summary(report, notes=notes)
        write_step_summary_if_configured(markdown)

        if outcome["hard_fail"]:
            failed = "; ".join(
                f"{f['league_code']} missing "
                + ", ".join(
                    f"{m['endpoint']} ({m['missing_count']}/{m['expected_count']})"
                    for m in f["missing_endpoints"]
                )
                for f in outcome["active_failures"]
            )
            msg += f" Active competitions incomplete: {failed}"
            return msg, 503

        return msg, 200
    except Exception as e:
        return f"Pipeline failed: {e}", 500
    finally:
        if lock_acquired:
            release_ingest_lock(client, run_id)
        _bind_quota_error_sink(None)
