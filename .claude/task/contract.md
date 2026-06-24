# Task contract — #500 metric-layer consolidation — PR-a (catalogue restructure + metric-layer naming, MVP-safe)

> This is PR-a of the NON-GATED full #500 consolidation. The end-state (locked target
> below) is ONE metric layer — the catalogue as the single registry, the LIVE MVP migrated
> onto it, the legacy seed deleted. NONE of it is #391-gated. The merge IS the deliverable
> and happens in this same work stream (PR-d), not "later". The work is sequenced into
> reviewed PRs purely for reviewability and MVP-safety, not deferral. MVP-safety is enforced
> by a CHECK, not by gating: at every step the generated `site/match-preview/metric_definitions.json`
> must stay BYTE-IDENTICAL to today's. PR-a touches ZERO live-chain files, so it is trivially safe.

objective: >
  Apply the locked one-name scheme to the metric layer across the metric_catalogue / v2 consumers
  (catalogue seed, the int metric models, the benchmark macros, the v2 marts, the no-drift guard,
  tests, the v2 export refs) and restructure the catalogue (entity-value normalisation + the
  CPO-locked de-dup). Rename the player-side & v2-benchmark metric ids/columns at the metric-layer
  OUTPUT (shots_on_target -> shots_on_goal, goals_saves -> saves, goals_conceded -> goals_against,
  + per90/per_match variants). Repair the CSV corruption the prior WIP introduced (two merged rows).
  The ONE rename shared with the LIVE site (corners_conceded -> corners_against) lands in PR-d (the
  live merge), where the live chain is touched — sequencing, not gating. So PR-a leaves the live MVP
  byte-identical.
refs: >
  #500; the 2026-06-24 CPO lock (target block below); the 2026-06-25 CPO correction in
  `.claude/active_work.md` ("the merge is NOT deferred / NOT #391-gated; do the full consolidation now;
  MVP-safety = byte-identical metric_definitions.json, not deferral"); content_architecture.md §10.
  SoT-difference work (#565) is STASHED ("sot-difference WIP (paused for #500)"), re-added after #500.

# =====================================================================================
# REFERENCE — CPO-LOCKED TARGET (2026-06-24; the END-STATE, achieved across the PR sequence)
# =====================================================================================
# 0. ONE seed: consolidate metric_definitions.csv (legacy MVP) INTO metric_catalogue.csv; migrate the
#    live MVP onto it; retire the legacy seed + build + *_recent/*_pretournament i18n. (PR-d — NOW, not gated.)
# 1. metric_catalogue.csv is the single source of truth. metric_id == the model column that computes it.
# 2. entity values: team | player | team and player. De-dup the two dual rows (duels_won_pct,
#    finishing_efficiency) -> one "team and player" row each. [PR-a — CPO-locked; see D2.]
# 3. One term per stat (provider term kept when it is good football language):
#    - shots_on_goal  (NOT shots_on_target)
#    - saves          (NOT goals_saves — that is the API path, not football language)
#    - _against for every conceded stat: goals_against, corners_against (was corners_conceded),
#      shots_on_goal_against (was shots_on_target_faced / the team shots_on_target_against). _conceded/_faced retired.
# 4. Models named int_<entity>_<window>__metrics + consolidate the redundant team-season models. (PR-b.)
# 5. label_i18n_key in the catalogue is the single display spine; reconcile site i18n to it. (PR-d.)
# 6. One explainer doc (metric_layer.md); retire/fold player_metrics_catalogue.md + metrics_display.md. (PR-c.)
#
# CRITICAL DISCOVERY (2026-06-24, re-verified from source this session): there are TWO metric SEEDS /
# two parallel systems —
#   metric_catalogue.csv (v2; export_site_data.py + the v2 models; the v2 site #391 is PAUSED) and
#   metric_definitions.csv (LEGACY MVP; export_metric_definitions_json.py + build_match_preview_site +
#     site/match-preview + site/team-season = the LIVE site). metric_definitions.csv is a thin
#   UI-BINDING MANIFEST over the SAME metric identities the catalogue holds (per metric: home_/away_/
#   single_column bindings + a window suffix _recent/_pretournament/_form + a context match_preview/
#   wc_pretournament). That split IS the "2-3 metric layers". Never judge the metric layer from one seed.
#   PR-d facts (verified): the live JSON carries NO labels (format/context/columns only -> the byte check
#   is i18n-independent); live i18n keys are window-suffixed (metrics.<id>_recent) vs the catalogue's
#   metrics.<base>.label / playerMetrics.* (a real reconciliation); `qualifier_games_played` is a LIVE
#   metric NOT yet in the catalogue (PR-d must register it).
#
# PR SEQUENCE (each = its own PR + contract; ALL non-gated, executed in this work stream):
#   PR-a (THIS): catalogue restructure (entity values + de-dup) + the CSV-corruption repair + player/
#     v2-benchmark metric-id & column renames at the metric-layer OUTPUT + v2 consumers + no-drift guard
#     + tests + v2 export refs. corners_conceded -> PR-d. NO live-chain edits, NO model-file renames,
#     NO staging/base/core atom renames.
#   PR-b: model FILE renames -> int_<entity>_<window>__metrics + team-season consolidation + the deep
#     atom renames (staging/base/core goals_saves -> saves, goals_conceded -> goals_against) + drop the
#     no-drift guard's _season strip.
#   PR-c: doc consolidation (metric_layer.md; retire/fold player_metrics_catalogue.md + metrics_display.md).
#   PR-d (the merge — NOW): consolidate metric_definitions.csv INTO the catalogue; repoint
#     export_metric_definitions_json.py at the catalogue; delete metric_definitions.csv + the legacy
#     *_recent/*_pretournament i18n; corners_conceded -> corners_against END-TO-END on the live side;
#     reconcile i18n onto label_i18n_key; register qualifier_games_played. MVP-safety = byte-identical
#     metric_definitions.json at every step.

# =====================================================================================
# PR-a EXECUTION
# =====================================================================================

scope_paths:
  - .claude/task/**
  - .claude/active_work.md
  # --- the catalogue (source of truth) ---
  - dbt_project/seeds/metric_catalogue.csv
  # --- the metric-layer writers (int models that OUTPUT the renamed columns) ---
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_momentum__player.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__player.sql
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks__player.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks__team.sql
  # --- the macros (single-source metric->column maps the benchmarks read) ---
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/macros/team_benchmark_metrics.sql
  # --- the v2 marts that select the renamed columns ---
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_momentum__player.sql
  - dbt_project/models/5_marts/shared/mart_season_record__player.sql
  - dbt_project/models/5_marts/shared/mart_fixture_stats__player.sql
  - dbt_project/models/5_marts/shared/mart_player_match_log.sql
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__player.sql
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__team.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_season_record__team.sql
  # --- the schema/yml docs for the above models ---
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  # --- the no-drift guard (drops the goals_saves->saves normalisation; keeps the _season strip for PR-b) ---
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  # --- the v2 export literal refs (NOT a shim — see D4) ---
  - scripts/export_site_data.py
  # NOTE: the exact per-file occurrence list is confirmed during build by `dbt compile` + the no-drift
  # guard + sqlfluff + the catalogue conformance/uniqueness tests. Any file found to need a metric-layer
  # edit but not listed here is added by a clean-tree amendment, never edited silently. docs/metric_layer.md
  # reference-text is intentionally LEFT to PR-c (doc consolidation) unless a reviewer rules the stale ids
  # must not ship — see D5.

# EXPLICITLY OUT OF SCOPE (do not edit in PR-a):
#   LIVE chain (PR-d): site/**, dbt_project/seeds/metric_definitions.csv, scripts/build_match_preview_site.*,
#     scripts/export_metric_definitions_json.py, scripts/export_pages_data.py, scripts/export_matchday_json.py,
#     scripts/export_team_season_json.py, .github/workflows/{pages-match-preview,ci-ui}.yml, site/i18n/*.
#   LIVE-shared team marts (corners_conceded carrier — PR-d): mart_momentum__team, int_momentum__team,
#     mart_matchday_insights, mart_team_season_insights, int_momentum.yml, domestic_league.yml.
#   ATOM layer (PR-b): stg_apif__fixture_players, base_apif__fixture_players, fct_fixture_player_stats,
#     fct_fixture_team_stats, base_apif__fixture_statistics, int_legs__team_match, core.yml.

impact_map: >
  writers (models that OUTPUT a renamed metric column):
    - int_player_season__metrics: shots_on_target -> shots_on_goal; goals_saves -> saves;
      goals_conceded -> goals_against; shots_on_target_per90 -> shots_on_goal_per90.
    - int_player_season_position__metrics: same player renames (shots_on_target, goals_saves, +per90).
    - int_team_season__metrics: shots_on_target_per_match_season -> shots_on_goal_per_match_season
      (v2-benchmark column; NOT live — see boundary). corners_conceded_per_match_season LEFT (PR-d).
  downstream (dbt MCP `list int_player_season__metrics+ int_team_season__metrics+
    int_player_season_position__metrics+`, models only — PASTED evidence; re-confirmed by grep this session):
      int_competition_benchmarks__player, int_competition_benchmarks__team, int_player_career__metrics,
      mart_competition_benchmarks__player, mart_competition_benchmarks__team, mart_leaderboards,
      mart_player_career, mart_player_profile, mart_team_profile, mart_team_season, mart_team_season_insights.
    Of these: int_player_career__metrics selects only appearances/goals/assists (NOT a renamed column) — no edit.
    mart_team_season + mart_team_season_insights carry corners_conceded/atoms only (PR-d/atom) — NOT edited.
    The rest select renamed player/v2 columns -> edited (listed in scope_paths).
    Grep confirms goals_saves/goals_conceded also flow through int_momentum__player, int_season_record__player,
    int_legs__player_match and their player marts; those models alias their OWN output and only the SEASON
    models are catalogue-guarded, so the atom name (goals_saves/goals_conceded) survives there until PR-b
    (a deliberate, compile-clean split-brain — each model is internally consistent).
  LIVE BOUNDARY (the load-bearing finding):
    - The live MVP = match-preview (mart_matchday_insights) + team-season (mart_team_season_insights),
      registered by metric_definitions.csv, which carries TEAM metrics ONLY (no shots_on_target, no player
      metrics). Evidence: metric_definitions.csv rows + mart selects.
    - Of all locked renames, ONLY corners_conceded is live-shared (mart_momentum__team -> mart_matchday_insights
      live alias *_corners_conceded_per_match_recent; int_team_season__metrics -> mart_team_season_insights
      passthrough corners_conceded_per_match_season -> site/team-season). Landing it in PR-d (with the rest of
      the live merge) = zero live-chain edits in PR-a.
    - The player renames (shots_on_target/goals_saves/goals_conceded) and the team v2 shots_on_target_per_match
      reach ONLY v2/benchmark/leaderboard surfaces (export_site_data.py, gitignored v2 output), never the live MVP.
    - export_site_data.py is the v2 export (docstring: "does not touch ... the live Pages deploy; Output is a
      build artifact, gitignored"). So its two literal refs (shots_on_target at lines ~47/~52) are updated, no
      shim (D4). The live MVP is protected by leaving metric_definitions.csv + its chain untouched.
  layer_rules: check_layer_contract (no new per-competition staging dir — N/A); check_registry_var_sync
    (N/A, no registry change); the no-drift test assert_no_uncatalogued_season_metric (UPDATED: player season
    model now outputs `saves`, so its goals_saves->saves normalisation is removed; the _season strip stays for
    PR-b; a `team and player` catalogue row now satisfies both entity checks). Atoms unchanged, so
    staging/base/core layer rules untouched.
  deploy_order: single dbt build rebuilds the renamed models + their v2 downstream together (one run); no
    cross-deploy window. The live chain is untouched, so the 04:00 nightly's live export is unaffected.
    export_site_data.py output is gitignored / not committed (#391 paused), so no committed-artifact churn.
  blast_radius: NUMBERS = NONE. Every change is a column-alias / metric_id-string / metric_key-value rename
    (+ the CSV-corruption repair, which RESTORES two rows the WIP accidentally hid — no value change); no
    formula, denominator, or filter changes. The atoms feeding each renamed column are identical. Verified by:
    the renames are 1:1 string substitutions at the metric layer; dbt compile + the no-drift guard confirm
    every renamed column still resolves to the same catalogue id and the same upstream atom; the live byte
    check is moot (no live-chain file touched).

decisions_taken: >
  The 2026-06-24 CPO target block (points 0-6) is approved. The 2026-06-25 CPO correction
  (.claude/active_work.md) fixed the scope: the merge is NOT deferred / NOT #391-gated — the full
  consolidation runs now, sequenced into reviewed MVP-safe PRs. Pre-approved for PR-a: the player +
  v2-benchmark metric-id/column renames (shots_on_target -> shots_on_goal, goals_saves -> saves at the
  metric-layer boundary, shots_on_target_per90/_per_match variants, shots_on_target_faced ->
  shots_on_goal_against); entity-value normalisation to {team, player, team and player}; the CPO-locked
  de-dup of the two dual rows; updating the v2 consumers + the no-drift guard. These are mechanical
  applications of the lock. Repairing the prior WIP's CSV corruption (re-splitting the two merged rows so
  dribbles_success and goals_against are their own rows again) is a defect fix inside this scope.

decisions_reserved:
  - D1 (corners_conceded -> corners_against — sequenced to PR-d, decided-with-rationale; CPO may pull forward):
    corners_conceded is the ONLY locked rename shared with the LIVE site. Renaming it requires editing the
    live-boundary marts (mart_matchday_insights, mart_team_season_insights) + the live i18n. Those edits are
    exactly the live merge, so corners_conceded rides PR-d (the merge), keeping the live-chain churn in ONE
    reviewed PR rather than splitting it. This is sequencing, NOT the old "leave the live website alone /
    combine later" gating. Net: the catalogue keeps id `corners_conceded_per_match` for the PR-a/b/c window
    (deliberate, recorded). Flag if the CPO wants it pulled into PR-a.
  - D2 (de-dup — DECIDED by the CPO lock 2026-06-24, NOT re-opened): merging duels_won_pct and
    finishing_efficiency to one "team and player" row each is the CPO lock (active_work.md / prompt step 4:
    "de-dup the two dual rows to one team and player row each"). The WIP implements it: the player-specific
    rows are removed, the team rows become `team and player`, finishing_efficiency numerator goals_for ->
    goals (generic term reading correctly for both entities; the catalogue numerator is documentation, the
    formula lives in the models). RESIDUAL (recorded, not escalated — the lock says do not re-open): a single
    merged row carries ONE label_i18n_key; the WIP keeps the team key (metrics.finishing_efficiency.label /
    metrics.duels_won_pct.label) and drops the player key (playerMetrics.*). These are v2 i18n pointers on the
    PAUSED surface; the whole key scheme is reconciled in PR-d, so no live or test impact now. The no-drift
    guard's new `team and player` clause makes both the team and the player model columns map to the merged row.
  - D3 (goals_conceded -> goals_against, player — CONFIRMED in PR-a): the lock says "_against for every
    conceded stat: goals_against". The player metric_id/column goals_conceded is renamed to goals_against at
    the int-model OUTPUT + the catalogue id now. The core ATOM goals_conceded (staging/base/core/fct + the
    momentum/season-record/legs int models) stays until PR-b. WIP applied the int-model output rename.
  - D4 (no export shim — premise confirmed from source): export_site_data.py is the v2 export (docstring:
    "does not touch ... the live Pages deploy; Output is a build artifact, gitignored"; #391 paused), NOT the
    live boundary. So no "translate new->old" shim; PR-a just updates its two literal metric refs
    (_LEADERBOARD_METRICS / _LB_KEEP: shots_on_target -> shots_on_goal). The live MVP is protected by leaving
    metric_definitions.csv + its chain untouched. This keeps "no translation layer" intact.
  - D5 (docs/metric_layer.md text — PR-c vs now): the explainer references some renamed ids. Default: leave
    to PR-c (doc consolidation). If a reviewer rules stale ids must not ship, fold the reference-only updates
    into PR-a via a clean-tree amendment.

done_when:
  - The CSV corruption is repaired: dribbles_success (player) and goals_against (player) are each their own
    row again; every catalogue row has the correct column count; the seed parses.
  - metric_catalogue.csv restructured (entity values normalised to {team, player, team and player}; renames
    applied; de-dup per D2) and every renamed model column / metric_key value aligned to the new ids across
    the in-scope files (the v2 marts + yml docs + benchmark macros + export refs).
  - `.venv/Scripts/dbt parse` and `dbt compile` clean; sqlfluff clean on the touched SQL; the no-drift guard
    (assert_no_uncatalogued_season_metric) passes — every metric column in the two season models maps to a
    catalogue (entity, metric_id); the catalogue uniqueness test and any benchmark/leaderboard catalogue-
    conformance test pass (confirm the deleted player rows do not break a metric_key conformance check; if one
    needs the `team and player` clause, that is a defect fix in scope).
  - `git diff --stat` shows ZERO changes under the OUT-OF-SCOPE live chain and atom layer (proof the live MVP
    is untouched), and the byte-identical metric_definitions.json holds trivially (metric_definitions.csv +
    its build untouched).
  - The G3 review cycle passes (Scope-Auditor + analytics-engineer + football-analytics for the catalogue rows);
    PR opened; CPO merges.

amendments: (none)
