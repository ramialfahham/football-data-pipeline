# Task contract — matches after extra time carry their score after extra time

objective: >
  The 26 matches after extra time whose provider score stops at 90 minutes get their score after
  extra time from fixture_result_corrections, each with two match reports on different sites. A
  test fails a match whose score stops at 90 minutes while an open-play goal or an own goal after
  minute 90 exists, so a new case is caught and corrected the same way.

refs: >
  #210 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/210): the defect,
  approved in chat, 2026-10-11. Corrections in the seed instead of a rule that infers the score
  from the goal events: approved in chat, 2026-10-11.

scope_paths:
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/tests/assert_extra_time_goals_counted_in_score.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_scores.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt seed loads fixture_result_corrections; base_apif__fixtures_next applies each row's
  official score and keeps the provider's beside it. Nothing else writes the score.
  downstream: `dbt ls --select fixture_result_corrections+ --resource-type model` on main gives 67
  models: base_apif__fixture_events base_apif__fixture_players base_apif__fixture_statistics
  base_apif__fixtures_next base_apif__players base_apif__teams base_apif__teams_global dim_player
  dim_player_team_season_mapping dim_team dim_team_competition_season_mapping fct_fixture
  fct_fixture_event fct_fixture_player_stats fct_fixture_team_stats int_legs__player_match
  int_legs__team_from_players int_legs__team_match int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_momentum__metrics int_player_profile__contribution int_player_profile__yoy
  int_player_season__metrics int_player_season__team int_player_season_position__metrics
  int_player_season_record int_team_competition_benchmark_metrics_long
  int_team_competition_benchmarks int_team_momentum__metrics int_team_momentum_window
  int_team_profile__streaks int_team_profile__yoy int_team_season__deserved_vs_actual
  int_team_season__metrics int_team_season__metrics_cumulative int_team_season_record
  mart_competition_fixtures mart_competition_index mart_competition_season_summary
  mart_fixture_standing_context mart_head_to_head mart_leaderboards mart_match_days
  mart_matchday_insights mart_next_matchday mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_match_log mart_player_momentum mart_player_profile
  mart_player_season_record mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_fixture_stats mart_team_fixtures mart_team_leaderboards mart_team_market_value
  mart_team_momentum mart_team_momentum_window mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record. The seed's own test,
  assert_result_corrections_applied, checks every row is applied and sourced.
  layer_rules: a seed is configuration; no model changes. Every other path in scope_paths is back
  at main's version: the branch's earlier approach is withdrawn.
  deploy_order: one dbt run; dbt seed precedes the models in data:build:main and fdp-nightly.
  blast_radius: the 26 matches' scores (8 this season, no result changes) and every listed model
  that carries a score, goals for and against, or form for those matches.

decisions_taken: >
  The defect and the corrections in the seed, each row with two match reports on different sites
  (source_kind match_reports) or an official record: approved in chat, 2026-10-11. The test is a
  detector: only open-play goals and own goals after minute 90 count as evidence, because the
  provider files some shoot-outs as penalty goals without the shoot-out label.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; fixture_result_corrections and its test exist.
  RECURRING COST: none.

decisions_reserved:
  - The shoot-out score (#178), the goal lists and the award kind in the seed (#176).

done_when:
  - dbt parse passes; sqlfluff on the test shows no finding.
  - Each of the 26 rows has two sources on different sites, read against the match.
  - The test's compiled SQL returns the 26 matches on today's fct_fixture and none with the seed's scores applied.
  - pytest tests/ passes; the offline CI gates pass; data:build:mr is green on the MR.

amendments: >
  Reworked from a rule that inferred the score from the goal events into seed corrections:
  approved in chat, 2026-10-11. The rule changed 15 shoot-outs the provider files as penalty goals
  after minute 120 (CI's corrections-share guard failed on Club World Cup 2020). Every model,
  document and test change of the rule's version returns to main's version.
