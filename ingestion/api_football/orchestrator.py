"""Top-level orchestrator: reads the competition registry and runs ingestion for each active competition.

Entry point for the Cloud Function (and local runs via main.py). Acquires a BigQuery
ingest lock to prevent concurrent runs, then iterates over selected competitions from
the registry. Results land in unified RAW_APIF_{entity} tables (shared by all competitions,
discriminated by the league_code STRING column) in the raw BigQuery dataset.

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
    load_prior_fixture_statistics_missing,
    persist_fixture_statistics_missing,
    run_ingest_completeness_checks,
    write_github_output,
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
from .ingest_plan import resolve_ingest_mode
from .loads.competition_runner import (
    run_cheap_phases,
    run_poll_phases,
    run_squads_for_competition,
    run_transfers_for_competition,
)
from .loads.batch_fixtures import run_batch_fixture_fanout_and_persist


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
        _fan_pri = (
            os.getenv("API_FOOTBALL_FANOUT_PRIORITY", "upcoming").strip() or "upcoming"
        )
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

        # Phase 1: full cheap phases or poll-only (catalog + latest-season fixtures).
        results = []
        for comp in selected:
            ingest_mode, ingest_reason = resolve_ingest_mode(ctx.client, comp)
            print(
                f"[api-football] league={comp.league_code} ingest_mode={ingest_mode} "
                f"reason={ingest_reason}",
                flush=True,
            )
            if ingest_mode == "poll":
                run_poll_phases(
                    ctx,
                    comp.league_code,
                    comp.provider_league_id,
                    current_season=comp.current_season,
                    history_seasons=comp.history_seasons,
                    season_type=comp.season_type,
                )
                continue
            result = run_cheap_phases(
                ctx,
                comp.league_code,
                comp.provider_league_id,
                current_season=comp.current_season,
                history_seasons=comp.history_seasons,
                season_type=comp.season_type,
            )
            if result is not None:
                results.append(result)

        # Phase 2: batch fixture sub-data fetch across all competitions.
        # Calls GET /fixtures?ids=ID1-...-ID20 (up to 20 per call) to retrieve
        # events, lineups, statistics, and players for finished fixtures.
        # Results land in RAW_APIF_{LC}_FIXTURE_DETAILS per competition.
        if results:
            run_batch_fixture_fanout_and_persist(ctx, results)

        # Phase 3: squad /players batch per competition
        for result in results:
            run_squads_for_competition(ctx, result)

        # Phase 4: transfers batch per competition (dated affiliation moves)
        for result in results:
            run_transfers_for_competition(ctx, result)

        msg = f"Loaded {ctx.tables_loaded} API-Football tables."
        if ctx.errors:
            uniq = _dedupe_errors_preserve_order(ctx.errors)
            shown = uniq[:40]
            tail = "; ".join(shown)
            if len(uniq) > 40:
                tail += f" ... (+{len(uniq) - 40} more distinct notes)"
            msg += f" Notes: {tail}"

        prior_stats_missing = load_prior_fixture_statistics_missing(client)
        report = run_ingest_completeness_checks(client)
        print(completeness_summary_line(report), flush=True)

        outcome = evaluate_completeness_outcome(
            report,
            prior_fixture_statistics_missing=prior_stats_missing,
        )
        persist_fixture_statistics_missing(client, report, run_id=run_id)

        # Always render the markdown summary so the per-competition coverage
        # state is visible on every workflow run page.
        notes: list[str] = []
        notes.append(f"Loaded {ctx.tables_loaded} API-Football tables.")
        if outcome["soft_partial"]:
            partial_codes = ", ".join(
                f"{p['league_code']} ({p['total_missing']} missing)"
                for p in outcome["soft_partial"]
            )
            notes.append(f"soft gate — backfill in flight: {partial_codes}")
        if outcome["stagnant_statistics"]:
            stagnant_codes = ", ".join(
                f"{s['league_code']} (stats missing {s['prior_missing_count']} → {s['missing_count']})"
                for s in outcome["stagnant_statistics"]
            )
            notes.append(
                f"STAGNANT statistics backfill (no progress since last run): {stagnant_codes}"
            )
        if outcome["hard_gated_failures"]:
            for f in outcome["hard_gated_failures"]:
                eps = ", ".join(
                    f"{m['endpoint']} ({m['missing_count']}/{m['expected_count']})"
                    for m in f["missing_endpoints"]
                )
                notes.append(f"hard gate incomplete: {f['league_code']} — {eps}")
        markdown = completeness_markdown_summary(report, notes=notes)
        write_step_summary_if_configured(markdown)
        write_github_output("new_data", "true" if ctx.tables_loaded > 0 else "false")

        if outcome["hard_fail"]:
            parts: list[str] = []
            if outcome["hard_gated_failures"]:
                parts.append(
                    "incomplete: "
                    + "; ".join(
                        f"{f['league_code']} missing "
                        + ", ".join(
                            f"{m['endpoint']} ({m['missing_count']}/{m['expected_count']})"
                            for m in f["missing_endpoints"]
                        )
                        for f in outcome["hard_gated_failures"]
                    )
                )
            if outcome["stagnant_statistics"]:
                parts.append(
                    "stagnant stats: "
                    + ", ".join(
                        f"{s['league_code']} ({s['missing_count']} unchanged)"
                        for s in outcome["stagnant_statistics"]
                    )
                )
            msg += " Completeness gate failed: " + "; ".join(parts)
            return msg, 503

        return msg, 200
    except Exception as e:
        return f"Pipeline failed: {e}", 500
    finally:
        if lock_acquired:
            release_ingest_lock(client, run_id)
        _bind_quota_error_sink(None)
