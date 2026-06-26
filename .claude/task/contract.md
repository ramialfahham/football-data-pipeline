# Task contract — #500 entity-first rename sweep (remaining `__team`/`__player` int+mart models)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Pure model rename (mirrors #574/#577); ZERO SQL logic change; numbers byte-identical by construction.

objective: >
  Finish #500's entity-first naming: rename the 8 models still on the old entity-suffix pattern
  (`<surface>__<entity>`) to the CPO-locked `<layer>_<entity>_<surface>` convention, across 3 surfaces
  (momentum_window, fixture_stats, competition_benchmarks), renaming each surface's int + mart together
  (mirrors #574/#577). Update every consumer (refs, yml name:, 2 DQ tests, the paused v2 export, docs).
  Excludes the `int_legs__*` family (separate naming question) and staging/base `*_apif__*` (source separator).
refs: #500 (entity-rename sweep); follows #574 (team) + #577 (player); CPO-approved plan 2026-06-26.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_momentum_window__team.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks__team.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks__player.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/5_marts/shared/mart_momentum_window__team.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum_window.sql
  - dbt_project/models/5_marts/shared/mart_fixture_stats__team.sql
  - dbt_project/models/5_marts/shared/mart_team_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_fixture_stats__player.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__team.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__player.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/shared/mart_player_match_log.sql
  - dbt_project/tests/assert_tournament_form_window.sql
  - dbt_project/tests/assert_momentum_window_matches_momentum.sql
  - scripts/export_site_data.py
  - dbt_project/docs/layering.md
  - docs/site_architecture.md
  - docs/competition_registry.yml
  - docs/competitions/wc26.md
  - docs/wireframes/99_gaps_register.md

impact_map: >
  writers: none new — the 8 renamed models write to new-named relations; each model's compiled SQL is
    byte-identical to its old-named self (pure rename, no logic change). The only edits inside files are
    the model name (file rename), ref() target updates to sibling renamed models, yml name:, and comments.
  downstream: EVIDENCE — `.venv/Scripts/dbt ls --project-dir dbt_project --resource-type model --select
    <the 8 models>+` (run 2026-06-26 on this branch) → the 8 models + int_team_momentum__metrics,
    mart_team_momentum, and mart_matchday_insights. NB mart_matchday_insights is the LIVE MVP mart; it is
    downstream TRANSITIVELY (int_momentum_window__team -> int_team_momentum__metrics -> mart_team_momentum /
    mart_matchday_insights) and does NOT directly ref any renamed model, so updating the single
    int_team_momentum__metrics ref to int_momentum_window__team keeps it byte-identical. Direct-ref consumers
    to update: int_team_momentum__metrics.sql; mart_momentum_window (its own int + both fixture_stats marts);
    the two competition_benchmarks marts (their int builder); the 2 DQ tests; the v2 export.
  layer_rules: none triggered — no model added/moved across layers; materializations unchanged (all
    table/view; none incremental); check_layer_contract + the no-drift guard unaffected (no metric column
    added/renamed; the renamed tests ride with their models).
  deploy_order: new-named relations built by ci-data-build (state:modified+); the 8 old relations orphan
    -> pending CPO bq rm (mirrors #574/#577). None incremental -> no --full-refresh. mart_matchday_insights
    (MVP) rebuilds from the renamed chain but byte-identical, so the live site is unaffected.
  blast_radius: zero numeric change anywhere (pure rename, byte-identical content); the paused v2 export's
    queries are updated atomically in this PR so it stays whole; the live MVP build reads MVP artifacts, none
    of the renamed marts.

decisions_taken: >
  CPO-approved plan (2026-06-26): full Option B — rename all 8 models (3 ints + 5 marts) across the 3
  surfaces, int+mart together, to the locked entity-first names. Exclude int_legs__* and staging/base.

decisions_reserved:
  - The int_legs__* family rename (entity-first target is genuinely ambiguous; ~15+ consumers) is a SEPARATE
    naming-design question, not decided here — flagged out of scope.
  - Target names are the mechanical application of the locked `<layer>_<entity>_<surface>` convention; if any
    target reads ambiguously on implementation, stop and escalate (§11) rather than choosing.

done_when:
  - `.venv/Scripts/dbt parse` clean (all renamed refs resolve).
  - Repo grep returns ZERO `(int|mart)_(momentum_window|fixture_stats|competition_benchmarks)__(team|player)`
    in live content (dbt/scripts/docs).
  - New-vs-prod byte-identical check on the renamed marts (FULL OUTER JOIN on grain, to_json_string) → 0 mismatches.
  - Routes to scope-auditor + analytics-engineer-reviewer (dbt_project/**) + cto-reviewer (scripts/export_*.py)
    + bi-analyst-reviewer (docs/wireframes/**) + data-engineer-reviewer (docs/competition_registry.yml).
    4-step review cycle → commit gate. CPO merges.

amendments:
  - 2026-06-26: + dbt_project/models/5_marts/shared/mart_player_match_log.sql — authority: the
    CPO-approved plan ("update every consumer; zero remaining old names in live content"). A missed
    sibling mart whose description names the renamed mart_fixture_stats__player; content = repoint that
    comment to mart_player_fixture_stats (no logic change). Amended on a code-clean tree (the sweep's code
    edits were stashed for the amendment, then restored), per the contract-gate clean-tree rule.
