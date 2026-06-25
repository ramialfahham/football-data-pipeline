# Task contract — #500 PR-b1: deep atom renames (saves / goals_against / shots_on_goal)

> Sliced from PR-b per CPO 2026-06-25 ("go ahead as recommended" — atom renames FIRST as one
> reviewable PR; the file renames + `_season`-suffix + team-season consolidation are a SEPARATE
> follow-up once the int_<entity>_<window>__metrics mapping is pinned). This PR is a pure 1:1
> COLUMN rename — no formula, grain, filter, or value change. See working_agreement §2/§7/§10/§11.

objective: >
  Apply the CPO-locked one-term-per-stat naming to the DEEP ATOMS end-to-end, eliminating the
  PR-a (#567) split-brain (the season __metrics models already OUTPUT saves/goals_against/
  shots_on_goal, but the underlying atoms + the momentum/season-record/legs/position models + the
  catalogue formula columns still use the API-path names):
  - player `goals_saves` -> `saves` (API path `$.goals.saves`; rename the column alias, keep the path)
  - player `goals_conceded` -> `goals_against`
  - team `shots_on_target_per_match` (the one remaining mart output alias) -> `shots_on_goal_per_match`
  Pure rename; the value each renamed column carries is identical.
refs: >
  #500 PR-b (sliced); CPO-locked naming (active_work.md ⭐#500 block + the PR-a reference block:
  `saves` not goals_saves, `_against` for conceded -> goals_against, `shots_on_goal` not shots_on_target).
  PR-a (#567) renamed the metric-layer OUTPUT but explicitly left the deep atoms + momentum/record/legs
  models to PR-b ("the core ATOM goals_conceded stays until PR-b").

scope_paths:
  - .claude/task/**
  - .claude/active_work.md
  # --- the atom origin: staging -> base -> core fact (+ schema doc) ---
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/3_core/core.yml
  # --- intermediate consumers (aligning the internal atom refs to the new name) ---
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_momentum__player.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__player.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  # --- player marts (renamed columns) ---
  - dbt_project/models/5_marts/shared/mart_fixture_stats__player.sql
  - dbt_project/models/5_marts/shared/mart_momentum__player.sql
  - dbt_project/models/5_marts/shared/mart_player_match_log.sql
  - dbt_project/models/5_marts/shared/mart_season_record__player.sql
  # --- the one team residual: mart output alias shots_on_target_per_match -> shots_on_goal_per_match ---
  - dbt_project/models/5_marts/shared/mart_momentum__team.sql
  # --- the catalogue: align the numerator/denominator FORMULA columns to the renamed atoms ---
  - dbt_project/seeds/metric_catalogue.csv

# EXPLICITLY OUT OF SCOPE (deferred per the locked sequence):
#   - model FILE renames (int_<entity>_<window>__metrics), team-season consolidation, the `_season`
#     suffix drop + the no-drift guard's `_season` strip — the SECOND PR-b slice (mapping not yet pinned).
#   - catalogue `label_i18n_key` + `description` prose (still say "shots on target"/"goals conceded") —
#     display/i18n, reconciled in PR-c (docs) / PR-d (i18n). PR-b1 touches only the machine-readable
#     numerator/denominator atom references.
#   - the no-drift guard: its ONLY `goals_saves` mention is a historical comment (accurate) — left.
#   - the LIVE chain + team-feed atoms (shots_total etc.) — untouched.

impact_map: >
  WRITERS (atom origin): the alias is set at the staging extraction
  stg_apif__fixture_players (`$.goals.saves as saves`, `$.goals.conceded as goals_against` — JSON
  path unchanged, only the column alias) -> base_apif__fixture_players -> fct_fixture_player_stats
  (core fact; INCREMENTAL, on_schema_change='sync_all_columns') + core.yml.
  DOWNSTREAM (renamed in lockstep; full source occurrence set from grep, PASTED 2026-06-25):
    goals_saves = 15 source files, goals_conceded = 14, shots_on_target = 2 (excl. target/ + logs/
    build artifacts). Consumers: int_legs__player_match, int_momentum__player, int_season_record__player,
    int_player_season_position__metrics, int_player_season__metrics; marts mart_fixture_stats__player,
    mart_momentum__player, mart_player_match_log, mart_season_record__player. (These already OUTPUT
    saves/goals_against from PR-a but referenced the OLD atom internally — PR-b1 aligns the internal
    refs so one name flows end-to-end.) Plus mart_momentum__team's lone output alias
    shots_on_target_per_match -> shots_on_goal_per_match. Plus metric_catalogue.csv numerator/denominator.
    No orphan references — `dbt compile` resolves every ref; grep for the old names returns clean
    (excl. the deferred i18n-key/description prose + the guard's historical comment).
  LIVE BOUNDARY (zero live-MVP impact): goals_saves/goals_conceded are PLAYER GK atoms that feed ONLY
    the v2/paused player surfaces. The live MVP is team-only — mart_matchday_insights (team form, via
    int_legs__team_from_players which aggregates key_passes/tackles/duels, NOT goals_saves/conceded) +
    mart_team_season_insights. shots_on_target_per_match is a v2 mart alias NOT selected by
    mart_matchday_insights (the live preview reads goals/shots/shot_accuracy/.../save_ratio, not it),
    and the v2 export is gitignored/paused. So NO live number or column moves.
  LAYER_RULES: check_layer_contract (no new staging dir — N/A); the no-drift guard
    (assert_no_uncatalogued_season_metric) is unaffected — the two guarded season __metrics models
    already OUTPUT saves/goals_against (PR-a), so the internal atom rename changes no OUTPUT column.
    base stays a view; the core fact stays incremental.
  DEPLOY_ORDER (the load-bearing note): ci-data-build runs `target: ci` -> dataset dbt_analytics
    (ISOLATED from prod) on PRs, so the PR's data-build does NOT touch the prod incremental fact.
    PROD is built by the scheduled run (dbt-scheduled, 04:00). fct_fixture_player_stats is incremental
    with on_schema_change='sync_all_columns' -> a normal incremental run after this rename would DROP
    goals_saves/goals_conceded and ADD saves/goals_against as NULL for all HISTORICAL rows (only new
    rows populated). So the deploy REQUIRES a one-time `dbt run --full-refresh --select
    fct_fixture_player_stats` at/after merge (the downstream tables/views then rebuild clean from the
    refreshed fact). WITHOUT the full-refresh, historical player saves/goals_conceded silently go NULL.
    This is flagged prominently in the PR body for the CPO to coordinate with the merge.
  BLAST_RADIUS: NUMBERS = NONE — pure 1:1 column rename (same JSON source path, same formula, same
    grain, same filters). Every renamed column resolves to the identical atom value. Verified by:
    the change is a token substitution; `dbt compile` resolves all refs; the live boundary is untouched.

decisions_taken: >
  The rename TARGETS are CPO-locked (saves / goals_against / shots_on_goal — active_work.md ⭐#500 +
  the PR-a reference block). The slice (atom renames first, file renames deferred) is the CPO's
  2026-06-25 "go ahead as recommended". This PR is mechanical: rename the column identifiers end-to-end
  and align the catalogue's numerator/denominator FORMULA columns (machine-readable atom refs) to the
  new names. The catalogue label_i18n_key + descriptions (display) and the model FILE renames /
  `_season` suffix / consolidation are DEFERRED per the locked sequence. No formula/grain/value change,
  so the football-analytics review is of a pure rename (no metric redefinition).
  COLLISION RULING (CPO 2026-06-25, escalations.log): in mart_player_match_log the locked player rename
  goals_conceded->goals_against clashes with an EXISTING goals_against = the team match-scoreline (used
  for W/D/L), a distinct concept. The player goals_conceded there is the goalkeeper's conceded, which in
  a per-match log equals the match goals_against already shown -> the CPO ruled DROP the redundant player
  goals_conceded column from mart_player_match_log (keep the keeper's saves [goals_saves->saves] + the
  unchanged match goals_against). NO new identifier invented. This is the ONLY file with the collision.

decisions_reserved:
  - D1 (DEPLOY, flagged — not a §10 product decision): the incremental-fact column rename needs a
    one-time `--full-refresh` of fct_fixture_player_stats at/after merge (see deploy_order). Standard
    rebuild of an existing fact (not a history/cadence/scope change), so no cost-gate escalation; but
    it MUST be coordinated with the merge or it NULLs historical player GK data. Flagged in the PR.
  - D2 (file-rename mapping — DEFERRED to the next slice, genuinely §10): which current files map to
    int_<entity>_<window>__metrics (do the momentum BUILDERS rename? do int_season_record__* / the
    position model rename?), the `_season`-suffix disposition, and what consolidation remains. NOT
    decided here — to be pinned with the CPO before the second slice.

done_when:
  - goals_saves->saves, goals_conceded->goals_against applied end-to-end across staging/base/core/int/
    marts + the catalogue numerator/denominator; mart_momentum__team's shots_on_target_per_match ->
    shots_on_goal_per_match. `grep -rn 'goals_saves\|goals_conceded' dbt_project/models dbt_project/seeds`
    returns clean (excl. the guard's historical comment); shots_on_target remains only in the deferred
    catalogue i18n-key/description prose.
  - `.venv/Scripts/dbt parse` + `dbt compile` clean; `sqlfluff lint` clean on touched SQL; the no-drift
    guard + the catalogue uniqueness/conformance tests pass; the catalogue numerator/denominator
    reference only existing columns. NO local full BQ build (shared warehouse).
  - The PR body PROMINENTLY flags the --full-refresh deploy requirement for fct_fixture_player_stats.
  - G3 review (scope-auditor + analytics-engineer-reviewer + football-analytics-expert-reviewer for the
    catalogue); PR opened; CPO merges + coordinates the full-refresh. Never self-merge.

amendments: (none)
