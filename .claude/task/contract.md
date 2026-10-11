# Task contract — matches after extra time carry their score after extra time

objective: >
  A match decided after extra time carries its score after extra time, the shoot-out excluded.
  Where the provider's score stops at 90 minutes while its goal events hold the extra-time goals,
  a new base model takes the score from the goal events, and every model that reads the score
  reads it from there.

refs: >
  #210 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/210): the defect and
  its plan, approved in chat, 2026-10-11.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_scores.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_extra_time_goals_counted_in_score.sql
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: base_apif__fixtures_next (the provider's score and the fixture_result_corrections seed)
  and base_apif__fixture_events (the goal events) feed the new base_apif__fixture_scores. Three
  models switch their score to it: fct_fixture, base_apif__fixture_statistics and
  base_apif__fixture_players. So do the two singular tests that check those stats models'
  cleaning, assert_base_team_stats_cleaned and assert_base_player_stats_cleaned.
  assert_result_corrections_applied keeps reading base_apif__fixtures_next, the model whose
  corrections seed it checks. Nothing else changes its SQL; `grep -rln base_apif__fixtures_next
  dbt_project/tests dbt_project/models` filtered to files reading goals_home/goals_away lists
  exactly these.
  downstream: `dbt ls --select fct_fixture+ base_apif__fixture_statistics+
  base_apif__fixture_players+ --resource-type model` gives 54 models: base_apif__fixture_players
  base_apif__fixture_statistics fct_fixture fct_fixture_player_stats fct_fixture_team_stats
  int_legs__player_match int_legs__team_from_players int_legs__team_match
  int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_momentum__metrics int_player_profile__contribution
  int_player_profile__yoy int_player_season__metrics int_player_season__team
  int_player_season_position__metrics int_player_season_record
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season_record mart_competition_fixtures
  mart_competition_index mart_competition_season_summary mart_fixture_standing_context
  mart_head_to_head mart_leaderboards mart_match_days mart_matchday_insights mart_next_matchday
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats
  mart_player_match_log mart_player_momentum mart_player_profile mart_player_season_record
  mart_team_competition_benchmarks mart_team_fixture_stats mart_team_fixtures
  mart_team_leaderboards mart_team_momentum mart_team_momentum_window mart_team_profile
  mart_team_season mart_team_season_insights mart_team_season_record.
  layer_rules: base may ref its own layer (layering.md, the ref rule); check_layer_contract.py
  forbids a base ref to dim_/fct_/int_/mart_ models and any per-model materialized config; the
  new model takes the folder's materialisation.
  deploy_order: one dbt graph; the new model builds before its three readers in the same run, in
  data:build:main on merge and in the 04:00 fdp-nightly. No staged migration.
  blast_radius: the 41 matches after extra time whose score the rule changes (8 this season, 14
  with a different result), in fct_fixture and every listed model that carries a score, a result,
  goals for and against, or form for those matches. Measured by a before/after query of the new
  model's compiled SQL against prod: exactly those 41 scores change and no other; the list goes on
  the MR.

decisions_taken: >
  The issue's plan, approved in chat, 2026-10-11: a base model base_apif__fixture_scores takes a
  match's score from its goal events where the match ended after extra time, the official-result
  seed does not correct it, the goal events of the first 90 minutes equal the provider's score,
  goal events after minute 90 exist, and no goal event lacks a minute. Goal events are goals,
  penalties and own goals with a player, shoot-out kicks left out. fct_fixture and the two
  base stats models read the score from it. cleaning_rules.md states the rule; the result rule
  there names goal events after extra time beside the league's official decision.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; a base cleaning model, the pattern
  base_apif__fixtures_next already follows with its corrections seed. RECURRING COST: one more
  base table built in each nightly from two base tables; its read is measured by dry-run before
  commit and recorded on the MR.

decisions_reserved:
  - Goal mismatches that are not extra-time scores, and the goal lists (#176).
  - The shoot-out score (#178).

done_when:
  - dbt parse passes; sqlfluff on the changed models shows no finding that main does not show.
  - The new model's compiled SQL, run as a query, changes exactly the 41 matches' scores.
  - The new test's compiled SQL returns the 41 matches on today's fct_fixture and none on the new model's scores.
  - pytest tests/ passes; the offline CI gates pass; data:build:mr is green on the MR.

amendments: >
  dbt_project/tests/assert_base_team_stats_cleaned.sql and
  dbt_project/tests/assert_base_player_stats_cleaned.sql join: authority, the approved plan's
  step that the stats models read the corrected score (approved in chat, 2026-10-11); the tests
  that check those models' cleaning must read the same score. Found by the
  analytics-engineer-reviewer in round 1: both still read the 90-minute score from
  base_apif__fixtures_next and would fail the 41 matches. Content: each test's fixtures CTE takes
  goals_home and goals_away from base_apif__fixture_scores.
