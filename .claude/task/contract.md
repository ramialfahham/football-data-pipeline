# Task contract — materialisation: one strategy, written once, true in the code

objective: >
  Every dbt model is a table, set once per layer in dbt_project.yml; the single exception is
  `incremental` for a core fact whose source delivers only a per-run delta (today the three fan-out
  facts). The 13 views become tables, the 52 per-model `table` configs that repeat the layer
  default are removed, check_layer_contract.py and its test enforce the rule on all five layers,
  and the rule is written once, in dbt_project/docs/layering.md §Materialisation, with every other
  document pointing to it.

refs: >
  The CPO's request in chat to start with layering.md and materialisation, and his instruction to
  act as the expert on the strategy; the plan he approved in chat. Measured before any edit
  (read-only, job history, last 14 days): tests on the 13 views billed about 211 GiB in prod over
  13 days; building all 13 as tables scans about 0.5 GiB (dry run).

scope_paths:
  - dbt_project/models/3_core/dim_coach.sql
  - dbt_project/models/3_core/dim_coach_team_mapping.sql
  - dbt_project/models/3_core/dim_competition_season.sql
  - dbt_project/models/3_core/dim_country.sql
  - dbt_project/models/3_core/dim_date.sql
  - dbt_project/models/3_core/dim_league.sql
  - dbt_project/models/3_core/dim_player.sql
  - dbt_project/models/3_core/dim_player_team_season_mapping.sql
  - dbt_project/models/3_core/dim_region.sql
  - dbt_project/models/3_core/dim_team.sql
  - dbt_project/models/3_core/dim_team_competition_season_mapping.sql
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/fct_standings.sql
  - dbt_project/models/3_core/fct_team_market_value_snapshot.sql
  - dbt_project/models/3_core/fct_transfer.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__standings_primary.sql
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs__team_from_players.sql
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_season__team.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__streaks.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/team/int_team__market_value_latest.sql
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/shared/mart_competition_index.sql
  - dbt_project/models/5_marts/shared/mart_competition_season_summary.sql
  - dbt_project/models/5_marts/shared/mart_fixture_standing_context.sql
  - dbt_project/models/5_marts/shared/mart_head_to_head.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_player_match_log.sql
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/mart_roster.sql
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_team_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_team_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_team_market_value.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum_window.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_season.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/docs/layering.md
  - dbt_project/docs/engineering_standards.md
  - dbt_project/dbt_project.yml
  - CLAUDE.md
  - AGENTS.md
  - docs/roles/analytics_engineer.md
  - .cursor/rules/dbt.mdc
  - scripts/check_layer_contract.py
  - tests/test_materialisation_policy.py
  - .claude/agents/analytics-engineer-reviewer.md
  - docs/data_contract.md
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

protected_override: >
  .claude/agents/analytics-engineer-reviewer.md: remove the word "(views)" after "base = first
  logic/dedup", which contradicts the base layer being a table. Approved by the CPO in chat through
  the plan, whose line reads: "`.claude/agents/analytics-engineer-reviewer.md` says base is
  "(views)", which is wrong; fixed by removing that word. Approving this plan approves that edit."
  (approved 2026-09-29, in chat, through the plan). The MR head's `Locked files:` line repeats this
  quote.

impact_map: >
  writers: each model is written only by its own SQL file; no model's SELECT changes. The only
  model change is the removal of a first-line `{{ config(materialized=...) }}` in 65 files.

  effect per model: 52 models carried `config(materialized='table')`, the same value as their
  layer default in dbt_project.yml (3_core, 4_intermediate, 5_marts all `+materialized: table`),
  so their materialisation does not change. 13 carried `config(materialized='view')` and become
  tables: int_team__market_value_latest, int_team_competition_benchmark_metrics_long,
  mart_leaderboards, mart_team_leaderboards, mart_matchday_insights, mart_standings, mart_roster,
  mart_team_fixtures, mart_team_market_value, mart_team_season_record, mart_player_season_record,
  mart_team_competition_benchmarks, mart_player_competition_benchmarks. The three incremental
  facts (fct_fixture_event, fct_fixture_player_stats, fct_fixture_team_stats) are untouched.

  downstream, dbt: `dbt ls --project-dir dbt_project --resource-type model --output name --select
  "<model>+"`, per converted model, downstream models only:
  int_team__market_value_latest -> mart_team_market_value;
  int_team_competition_benchmark_metrics_long -> int_team_competition_benchmarks,
  mart_team_competition_benchmarks;
  mart_standings -> mart_fixture_standing_context, mart_matchday_insights;
  mart_leaderboards, mart_team_leaderboards, mart_matchday_insights, mart_roster,
  mart_team_fixtures, mart_team_market_value, mart_team_season_record, mart_player_season_record,
  mart_team_competition_benchmarks, mart_player_competition_benchmarks -> no downstream models.
  Every reader refs the relation by name, which does not change.

  downstream, outside dbt: `grep -rlw <model>` over scripts, site_v2/src (committed data excluded),
  site_v2/scripts and ingestion: mart_leaderboards, mart_team_leaderboards, mart_team_season_record,
  mart_player_competition_benchmarks -> export_site_data.py; mart_matchday_insights ->
  export_matchday_json.py, export_pages_data.py, export_site_data.py, gen_domestic_marts.py;
  mart_standings -> export_site_data.py, StandingsTable.astro, types.ts; mart_roster,
  mart_team_fixtures -> export_site_data.py, check-page-specs.test.mjs, types.ts;
  mart_team_competition_benchmarks -> export_site_data.py, types.ts;
  int_team__market_value_latest -> check_description_hygiene.py (a name check, not a reader);
  int_team_competition_benchmark_metrics_long, mart_team_market_value, mart_player_season_record ->
  none. The export reads each by dataset.table name and selects columns, never the relation type,
  so a table serves it as the view did; the site reads the export's JSON, not the warehouse.

  row content: unchanged, with two stated exceptions. (1) Values that depend on unbroken ties
  (#183) can differ between builds as before; a table no longer changes them between reads.
  (2) Three models filter on `current_date()` (mart_matchday_insights.sql:81,
  mart_team_season_record.sql:26, mart_player_season_record.sql:25). As views the date was the
  day of the read; as tables it is the day of the build, as for their table siblings
  (mart_next_matchday, int_team_momentum_window, mart_team_momentum). Read the same day as the
  nightly they are identical; after a failed nightly they keep the last build's cut.

  layer_rules: check_layer_contract.py gains the same no-per-model-setting rule for 3_core,
  4_intermediate and 5_marts, with `incremental` the one value allowed in 3_core.

  protected path: the reviewer brief is read only by the analytics-engineer-reviewer agent when it
  is spawned; removing a wrong word changes no gate, hook or routing.

  deploy_order: the MR's data:build:mr rebuilds the 65 models and their downstream once in the MR's
  own ci_mr datasets; the merge's data:build:main is the full prod build every merge already runs.

  blast_radius: object type of 13 relations (view to table); BigQuery cost, measured: tests on the
  13 views billed about 211 GiB in prod over 13 days, about 16 GiB a day; one build of all 13 as
  tables scans about 0.5 GiB (dry run). No metric value changes.

decisions_taken: >
  The CPO approved the plan in chat: every layer table, set once per layer; `incremental` only for
  a core fact whose source delivers a per-run delta; no views, no ephemeral, no per-model setting
  elsewhere; the 13 views converted after the cost was measured and found to go down; the 52
  repeated `table` configs removed; the check extended to all five layers; the rule written once in
  layering.md with pointers elsewhere; the protected reviewer-brief word removed.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none — an existing check extended to three more layers.
  RECURRING COST: down, measured — see blast_radius.

decisions_reserved:
  - The tie-breaks that make some values differ between builds: #183, not here.

done_when:
  - dbt ls lists every model as table except the three incremental facts.
  - check_layer_contract.py passes, and fails on a model in 3_core, 4_intermediate or 5_marts that
    sets a per-model materialisation (watched red), and on a core model setting anything but
    incremental.
  - pytest tests/test_materialisation_policy.py and the full suite pass; the governance gates and
    dbt parse pass.
  - An independent agent confirms no file other than layering.md states a materialisation rule,
    other than the enforcement code and the pinned token sites.
  - review.md binds the staged hash with every routed verdict PASS.
  - Before the merge: the MR's data:build:mr builds the 13 as tables, and each is compared with the
    prod view (same rows, same values except the #183 ties); the result in the MR head.

amendments:
  - 2026-09-29: + docs/data_contract.md, tests/test_no_decision_history_in_docs.py — authority: the
    CPO's approved plan (the rule written once, with no history; other documents point to it) and
    the standing rule that a reference an approved change breaks is part of that change; content:
    data_contract.md's two sentences restating staging's materialisation with issue history become
    a pointer to layering.md §Materialisation, and the decision-history pin is lowered for the
    documents this change cleaned.
