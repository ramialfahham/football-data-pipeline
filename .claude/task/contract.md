# Task contract — #500 PR1: team metric consolidation (season-model merge + inline formulas + compose + entity-first model names)

> Governance G2/G3 contract. Written on a clean tree BEFORE any code edit.
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (escalation).

objective: >
  Consolidate the TEAM metric layer, MVP-safe and numbers byte-identical:
  (1) MERGE the duplicate season aggregation — `int_team_season__metrics` (whole season) becomes the
      FINAL-ROW PROJECTION of the cumulative `int_team_season_record` (renamed from int_season_record__team)
      instead of re-summing the legs a second time;
  (2) DE-DUPLICATE the formulas WITHOUT a macro (plain SQL + the compose pattern — CPO 2026-06-25):
      the whole-season metrics are computed ONCE (plain inline SQL) in int_team_season__metrics, and
      mart_team_season_record COMPOSES it (reuses the rollup, renames `_season`->display) rather than
      recomputing; mart_team_momentum keeps its own inline last-5 metrics (a genuinely different window);
  (3) entity-first MODEL renames (CPO-approved naming): int_momentum__team -> int_team_momentum__metrics,
      int_season_record__team -> int_team_season_record, mart_momentum__team -> mart_team_momentum,
      mart_season_record__team -> mart_team_season_record. (Player side = separate PR; the `_season` COLUMN
      drop = deferred to the live-surface PR because it changes the live JSON contract — see decisions_reserved.)
refs: #500 (metric-layer consolidation). CPO-approved this split 2026-06-25 ("Do it").

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_momentum__team.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__team.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/5_marts/shared/mart_momentum__team.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/mart_season_record__team.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/mart_momentum_window__team.sql
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/tests/assert_tournament_form_window.sql
  - dbt_project/tests/assert_momentum_window_matches_momentum.sql
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - dbt_project/models/4_intermediate/shared/int_momentum_window__team.sql
  - dbt_project/models/4_intermediate/shared/int_momentum__player.sql
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/docs/layering.md
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/4_intermediate/world_championship/wc/int_wc.yml
  - scripts/export_site_data.py

impact_map: >
  writers / lineage (from `dbt ls --select int_team_season__metrics+ int_momentum__team+
  int_season_record__team+` + grep of every ref):
    - FOUNDATION (unchanged): int_legs__team_match (one row per team per finished match; carries own +
      opponent stats incl. opponent_shots_total) -> all three window aggregators.
    - int_momentum__team (last-5 raw sums) -> ONLY mart_momentum__team. Rename -> int_team_momentum__metrics;
      update that one ref.
    - int_season_record__team (per-match cumulative raw sums) -> mart_season_record__team + int_team_profile__yoy.
      Rename -> int_team_season_record; ADD opponent_shots_total + league_sk + season_sk (already in the leg) so
      the projection can produce everything; update both refs.
    - int_team_season__metrics (whole-season; today RE-SUMS the legs) -> int_competition_benchmarks__team
      (via team_benchmark_metrics macro), mart_team_season, mart_team_profile, mart_team_season_insights,
      assert_no_uncatalogued_season_metric. It BECOMES the final row of int_team_season_record (plus inline
      formulas); OUTPUT COLUMNS (incl. the `_season` suffix) are UNCHANGED, so ALL its consumers are UNTOUCHED.
    - mart_momentum__team -> mart_matchday_insights (LIVE), 2 DQ tests, export_site_data.py (v2). Rename ->
      mart_team_momentum; update those 4 refs. mart_season_record__team -> export_site_data.py (v2) only.
  layer_rules: check_layer_contract — intermediate may not ref marts (unchanged); base views (untouched).
    The renamed builders stay intermediate tables; marts stay tables/views as-is.
  deploy_order: NO incremental facts touched — every model here is a full-refresh table or view, so NO
    --full-refresh dance. After merge, the renamed models build under their new names; the OLD-named relations
    (int_momentum__team, int_season_record__team, mart_momentum__team, mart_season_record__team) become
    ORPHANED tables in BQ (nothing refs them) — harmless, flagged for a one-time manual drop post-merge.
  blast_radius: NUMBERS BYTE-IDENTICAL. The merge sums the SAME legs (projection = today's whole-season
    aggregate); the inline formulas match the marts' field-by-field; the renames carry the same data under
    new names. LIVE JSON UNCHANGED: model names are not in the JSON; mart_matchday_insights output columns
    are unchanged (ref-rename only); the `_season` COLUMN names are KEPT (the projection still emits them) so
    mart_team_season_insights -> live team_season_insights.json is byte-identical. PROVED: a row-level JSON
    value check of the new projection vs prod int_team_season__metrics over ALL 12,537 team-seasons x 48
    columns = 0 mismatches (after fixing 2 subtleties found by the check: gate the 9 displayed team-feed
    sum columns on partial coverage; gate shot_accuracy on team coverage too, not just SoT).

decisions_taken: >
  - NO macro (CPO 2026-06-25 — macros decrease maintainability). The shared formulas are plain INLINE SQL in
    the explicit mart form (`case when <coverage> < <games> then null else safe_divide(stat, <coverage>) end`),
    value-equivalent to the old season model (full coverage => total == coverage; partial => both NULL) —
    verified byte-identical. De-duplication is by COMPOSITION: mart_team_season_record reuses
    int_team_season__metrics (renaming `_season`->display) instead of recomputing; only the genuinely-different
    last-5 window (mart_team_momentum) keeps its own inline copy. int_team_season__metrics exposes two extra
    NON-metric columns for that compose — entity_type + games_with_team_stats — both exempt in the no-drift guard.
  - Window-SPECIFIC metrics stay INLINE in their own model (they are not duplicated): shot_share +
    points_capture (season only), clean_sheets-as-count vs -as-rate.
  - Naming: entity-first per the CPO-approved convention (2026-06-25). The cumulative base stays a builder
    name (int_team_season_record, no __metrics). int_team_season__metrics keeps its name (established; correct
    under the scheme; renaming again = churn).

decisions_reserved:
  - The `_season` COLUMN-suffix drop is DEFERRED to the live-surface PR (PR-d): mart_team_season_insights
    feeds the live team-season page via `select *`, so the column names ARE the JSON keys; dropping `_season`
    changes the live data contract and must move in lockstep with the site JS. Do NOT drop it here.
  - The PLAYER consolidation (formula-dedup only; the two player season models do NOT merge — different grain +
    minutes/per-90s) is a SEPARATE PR. Not in scope.
  - The leftover suffix-style mart renames (mart_momentum_window__team, mart_fixture_stats__*,
    mart_competition_benchmarks__*) + the int_team_season__metrics folder move to shared/ = a follow-up sweep.
  - Dropping the orphaned old-named BQ tables post-merge (one-time manual `bq rm`) — CPO action, flagged.

done_when:
  - `dbt parse` + `dbt compile` clean; `sqlfluff lint models` clean on the touched models; the no-drift guard
    (assert_no_uncatalogued_season_metric) still passes (int_team_season__metrics output columns unchanged).
  - BYTE-IDENTICAL proof: a query comparing the NEW int_team_season__metrics (projection) against the CURRENT
    prod table joins on (team_sk, season_sk) and asserts every metric column is equal (or both null) for a
    sample of competition-seasons — zero mismatches. Same spot-check for mart_team_momentum vs mart_momentum__team
    and mart_team_season_record vs mart_season_record__team.
  - `python .claude/hooks/git_discipline.py --staged-hash` == review.md diff_sha256; scope-auditor +
    analytics-engineer-reviewer + cto-reviewer PASS (each >=2 named risks); no FAIL, no open ESCALATE.

amendments:
  - 2026-06-25: dropped the formula macro (`team_window_metrics`) — authority: CPO ("macros decrease
    maintainability; drop it"). Replaced by plain inline SQL + the compose pattern (above). + added
    `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` to scope: int_team_season__metrics now
    exposes entity_type + games_with_team_stats (so mart_team_season_record can compose it); both are
    NON-metric (a dimension + a coverage count), so they go in the guard's `exempt` set — consistent with
    the existing stat_coverage_season_games / player_stat_coverage_season_games exemptions.
  - 2026-06-25: + int_momentum_window__team.sql, int_momentum__player.sql, int_momentum_window.yml,
    dbt_project/docs/layering.md — authority: CPO "fold them in". Completing the rename: these 4 carry only PROSE
    references to the old names (int_momentum__team / mart_momentum__team / mart_season_record__team in
    comments + the layering.md mart inventory); updated to the new names so no stale mentions remain. No
    logic change.
