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
    load_prior_dropped_calls,
    load_prior_fixture_statistics_missing,
    load_prior_per_team_missing,
    PER_TEAM_ENTITIES,
    per_team_expectations_from_results,
    per_team_missing_by_league_entity,
    persist_fixture_statistics_missing,
    read_per_team_coverage,
    read_prior_snapshot,
    run_ingest_completeness_checks,
    skipped_exemption_note,
    write_ci_output,
    write_step_summary_if_configured,
)
from .coverage import read_coverage
from .ingestion_lock import (
    acquire_ingest_lock,
    ensure_ingest_lock_table,
    new_run_id,
    release_ingest_lock,
)
from .refetch import latest_ingest_per_league
from .settings import (
    DATASET_ID,
    DEFAULT_SEASON_WINDOW_YEARS,
    GCP_PROJECT_ID,
    _apply_ingest_profile_defaults,
    _env_truthy,
    _ingest_profile_name,
    get_headers,
    raw_table,
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
    minute_rate_limit_counts,
    reset_http_quota_exhausted,
    reset_minute_rate_limit_counts,
)
from .loads.context import PipelineContext
from .ingest_plan import resolve_ingest_mode
from .loads.competition_runner import (
    run_cheap_phases,
    run_poll_phases,
    run_squads_for_competition,
    run_player_squads_for_competition,
    run_player_squads_catchup,
    run_transfers_for_competition,
)
from .loads.squads import captured_player_team_seasons
from .loads.player_universe import query_player_universe
from .loads.player_profiles import load_player_profiles_global
from .loads.player_teams import load_player_teams_global
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
        reset_minute_rate_limit_counts()
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
            f"default_window_last_{DEFAULT_SEASON_WINDOW_YEARS}={_lo}-{_hi} "
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
        #
        # Fanout coverage is read ONCE here, for every league, and passed into the loop.
        # read_coverage() scans all of RAW_APIF_FIXTURE_DETAILS with no league or time
        # filter; it used to be reached from inside resolve_ingest_mode, i.e. once per
        # competition, which made ingestion reads O(competitions^2) — 45 scans of a
        # multi-GiB table every run, growing quadratically as leagues are added (#33 item 1).
        #
        # ⚠ This is deliberately NOT a run-wide cache. Phase 2 WRITES FIXTURE_DETAILS, and
        # the completeness check below MUST see those writes — that is what it checks. It
        # therefore keeps its own, separate read. Hoisting further (one read for the whole
        # run) would make every run report fanout gaps that the same run had just filled.
        phase1_covered = read_coverage(ctx.client)
        # #33 item 14 — the re-fetch cadence for coaches and transfers, read ONCE for every
        # league and passed into the loops below. Same reason as read_coverage above: reading
        # this per competition would reintroduce exactly the O(competitions^2) shape item 1
        # removed. Two grouped queries against tables 8b shrank to 0.178 and 0.008 GiB.
        #
        # Unlike phase1_covered this IS safe to hoist for the whole run: nothing in this run
        # writes COACHES or TRANSFERS before these loops, so there are no same-run writes for
        # a later read to miss.
        coaches_last_ingest = latest_ingest_per_league(ctx.client, raw_table("COACHES"))
        transfers_last_ingest = latest_ingest_per_league(ctx.client, raw_table("TRANSFERS"))
        results = []
        # Finished (poll-mode) comps + their teams, for the squad catch-up (Phase 3c).
        finished_comps: list[tuple[str, int, set[int]]] = []
        for comp in selected:
            ingest_mode, ingest_reason = resolve_ingest_mode(ctx.client, comp, phase1_covered)
            print(
                f"[api-football] league={comp.league_code} ingest_mode={ingest_mode} "
                f"reason={ingest_reason}",
                flush=True,
            )
            if ingest_mode == "poll":
                poll_result = run_poll_phases(
                    ctx,
                    comp.league_code,
                    comp.provider_league_id,
                    current_season=comp.current_season,
                    history_seasons=comp.history_seasons,
                    season_type=comp.season_type,
                )
                if poll_result is not None:
                    poll_team_ids, poll_season = poll_result
                    if poll_team_ids and poll_season is not None:
                        finished_comps.append((comp.league_code, poll_season, poll_team_ids))
                continue
            result = run_cheap_phases(
                ctx,
                comp.league_code,
                comp.provider_league_id,
                current_season=comp.current_season,
                history_seasons=comp.history_seasons,
                season_type=comp.season_type,
                coaches_last_ingest=coaches_last_ingest,
            )
            if result is not None:
                results.append(result)

        # Phase 2: batch fixture sub-data fetch across all competitions.
        # Calls GET /fixtures?ids=ID1-...-ID20 (up to 20 per call) to retrieve
        # events, lineups, statistics, and players for finished fixtures.
        # Results land in RAW_APIF_{LC}_FIXTURE_DETAILS per competition.
        if results:
            run_batch_fixture_fanout_and_persist(ctx, results)

        # Phase 3: squad /players batch per competition.
        #
        # The captured (team, season) set is read ONCE here rather than once per
        # competition. That query UNNESTs all of RAW_APIF_PLAYERS and was the second
        # O(competitions^2) read in this loop (#33 item 1). Unlike Phase 1's coverage
        # hoist this set is MUTATED as the loop writes, because this loader writes the
        # very table the set describes — see load_squad_players_batch.
        squads_captured = captured_player_team_seasons(ctx)
        for result in results:
            run_squads_for_competition(ctx, result, already_captured=squads_captured)

        # Phase 3b: /players/squads batch per competition (current squad + shirt number)
        for result in results:
            run_player_squads_for_competition(ctx, result)

        # Phase 3c: /players/squads catch-up for finished (poll-mode) competitions — capture
        # squads for teams whose comps have all finished and were not captured in-season, keyed
        # by team and deduped across comps (club + national). Quota-guarded; rides the daily run.
        active_team_ids: set[int] = set()
        for result in results:
            active_team_ids.update(result.team_ids)
        run_player_squads_catchup(ctx, finished_comps, active_team_ids)

        # Phase 4: transfers batch per competition (dated affiliation moves)
        for result in results:
            run_transfers_for_competition(
                ctx, result, transfers_last_ingest=transfers_last_ingest
            )

        # Phase 5: global per-player bio + career (profiles + teams) over the current
        # universe (players rostered season >= MIN_SEASON, gathered from RAW_APIF_PLAYERS;
        # already-ingested players skipped). Quota-guarded — the first run is the backfill,
        # resumed on later runs.
        #
        # Both loaders need the SAME player universe, and computing it UNNESTs all of
        # RAW_APIF_PLAYERS. Nothing writes that table between them — profiles writes
        # RAW_APIF_PLAYER_PROFILES, teams writes RAW_APIF_PLAYER_TEAMS — so the second
        # run of that query returned an identical answer for full price (#33 item 1).
        # A failure here is non-fatal: `universe=None` makes each loader compute its own,
        # which is exactly the previous behaviour.
        try:
            shared_universe = query_player_universe(ctx.client)
        except Exception as e:
            ctx.errors.append(f"player universe (shared): {e}")
            shared_universe = None
        load_player_profiles_global(ctx, universe=shared_universe)
        load_player_teams_global(ctx, universe=shared_universe)

        msg = f"Loaded {ctx.tables_loaded} API-Football tables."
        if ctx.errors:
            uniq = _dedupe_errors_preserve_order(ctx.errors)
            shown = uniq[:40]
            tail = "; ".join(shown)
            if len(uniq) > 40:
                tail += f" ... (+{len(uniq) - 40} more distinct notes)"
            msg += f" Notes: {tail}"

        # ONE read of the previous run's snapshot, three keys out of it. These three
        # readers each used to issue their own identical query (#33 item 1). Read BEFORE
        # persisting this run's counts, or every comparison is against itself.
        prior_snapshot = read_prior_snapshot(client)
        prior_stats_missing = load_prior_fixture_statistics_missing(client, prior_snapshot)
        prior_dropped = load_prior_dropped_calls(client, prior_snapshot)
        prior_per_team = load_prior_per_team_missing(client, prior_snapshot)
        dropped_calls = minute_rate_limit_counts()
        # #898 cause 3: the per-team endpoints (players, squads, transfers, coaches) had no
        # completeness check at all. Two-step read on purpose — see _latest_snapshot_timestamps.
        #
        # Expected comes from THIS RUN, not from BigQuery. `results` holds only the competitions
        # that ran the full phases; poll-mode ones never fetch teams, players, squads or transfers,
        # so they cannot be judged and must not appear. `team_ids` is the exact set the loaders
        # iterated and `max(seasons_list)` is the exact reference season
        # `load_squad_players_batch` was called with, so expectation and fetch cannot drift apart.
        per_team = read_per_team_coverage(
            client, per_team_expectations_from_results(results)
        )
        per_team_missing = per_team_missing_by_league_entity(per_team)
        report = run_ingest_completeness_checks(client)
        print(completeness_summary_line(report), flush=True)

        outcome = evaluate_completeness_outcome(
            report,
            prior_fixture_statistics_missing=prior_stats_missing,
            dropped_calls=dropped_calls,
            prior_dropped_calls=prior_dropped,
            per_team_missing=per_team_missing,
            prior_per_team_missing=prior_per_team,
            skipped_per_team=ctx.skipped_per_team,
        )
        # NEVER SILENT. The gate exempts pairs that were deliberately skipped this run (#33 item
        # 14's 7-day cadence), and an exemption nobody can see is how a real gap hides behind the
        # cadence. The text lives in `skipped_exemption_note` so a test can assert it — nothing
        # drives this function end to end.
        exemption_note = skipped_exemption_note(outcome.get("skipped_per_team_exempt"))
        if exemption_note:
            print(exemption_note, flush=True)
        persist_fixture_statistics_missing(
            client,
            report,
            run_id=run_id,
            dropped_calls=dropped_calls,
            per_team_missing=per_team_missing,
        )

        # Always render the markdown summary so the per-competition coverage
        # state is visible on every workflow run page.
        notes: list[str] = []
        notes.append(f"Loaded {ctx.tables_loaded} API-Football tables.")
        # #898: a run that dropped calls must not look like a clean one. Before this, ctx.errors
        # reached only a stdout line that was deduped and truncated at 40 entries, so 10 of 18
        # nightly runs reported success while dropping calls.
        if dropped_calls:
            notes.append(
                f"DROPPED {sum(dropped_calls.values())} API call(s) to the per-minute rate limit: "
                + ", ".join(f"{ep} {n}" for ep, n in dropped_calls.items())
            )
        if outcome["stagnant_dropped_calls"]:
            notes.append(
                "STAGNANT dropped calls (same endpoint two runs running): "
                + ", ".join(
                    f"{s['endpoint']} ({s['prior_count']} then {s['count']})"
                    for s in outcome["stagnant_dropped_calls"]
                )
            )
        # #898 cause 3. Reported on EVERY run, including COACHES, which never gates. Reporting a
        # number that never fails is the point: it is how a slow drift becomes visible before it
        # becomes a hole.
        per_team_notes = [
            f"{lc}/{entity} {info['missing_count']}/{info['expected_count']}"
            for lc, block in sorted(per_team.items())
            for entity in PER_TEAM_ENTITIES
            for info in [block.get(entity) or {}]
            if info.get("missing_count")
        ]
        if per_team_notes:
            notes.append("per-team teams MISSING: " + ", ".join(per_team_notes))
        if outcome["stagnant_per_team_gaps"]:
            notes.append(
                "STAGNANT per-team gaps (same league+entity two runs running): "
                + ", ".join(
                    f"{s['league_code']}/{s['entity']} ({s['prior_count']} then {s['count']})"
                    for s in outcome["stagnant_per_team_gaps"]
                )
            )
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
        write_ci_output("new_data", "true" if ctx.tables_loaded > 0 else "false")

        if outcome["hard_fail"]:
            parts: list[str] = []
            if outcome["stagnant_per_team_gaps"]:
                parts.append(
                    "per-team gaps not healing: "
                    + ", ".join(
                        f"{s['league_code']}/{s['entity']} "
                        f"({s['prior_count']} then {s['count']} teams missing)"
                        for s in outcome["stagnant_per_team_gaps"]
                    )
                )
            if outcome["stagnant_dropped_calls"]:
                # A single bad run stays green on purpose: the per-minute limit self-heals, and
                # failing skips the dbt build (every post-ingest step is gated on this step
                # succeeding), which would cost daily freshness. Two runs running means it is not
                # healing, and that IS worth a day of staleness. CPO decision, 2026-08-03.
                parts.append(
                    "dropped calls not healing: "
                    + ", ".join(
                        f"{s['endpoint']} ({s['prior_count']} then {s['count']})"
                        for s in outcome["stagnant_dropped_calls"]
                    )
                )
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
