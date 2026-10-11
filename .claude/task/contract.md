# Task contract — one goal definition

objective: >
  What counts as a goal is defined once, in base_apif__fixture_events, and every model and test
  that counts goals reads it: a Goal event (normal goal, penalty, own goal) that is not a
  shoot-out kick (the shoot-out label, or a negative minute), leaving out a goal event with
  neither scorer id nor scorer name where the match adds up without it. The same model decides
  once whether a match's events cover more than its goals. Staging reads the assist's player id;
  fct_fixture_event serves the goal flags and the assist; fct_fixture carries the award's kind and
  the score on the pitch from fixture_result_corrections.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the goals,
  step 1. The plan (one goal definition, then the goals on mart_competition_fixtures): approved in
  chat, 2026-10-11.

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_events.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_team_goal_split_adds_up_to_score.sql
  - dbt_project/tests/assert_extra_time_goals_counted_in_score.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt only. stg_apif__fixture_events reads RAW_APIF_FIXTURE_DETAILS; nothing else writes
  an event.
  downstream: `dbt ls --select stg_apif__fixture_events+ base_apif__fixtures_next+ --resource-type
  model` on main gives 68 models: stg_apif__fixture_events base_apif__fixture_events
  base_apif__fixture_players base_apif__fixture_statistics base_apif__fixtures_next
  base_apif__players base_apif__teams base_apif__teams_global dim_player
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
  mart_team_season_insights mart_team_season_record.
  layer_rules: the definition is cleaning, so it lives in base; core serves it; no mart changes.
  deploy_order: one dbt run.
  blast_radius: the matches whose goal events add up only with the cleaning: measured on prod, 19
  where a nameless goal event is left out and 5 with shoot-out kicks at a negative minute. Their
  team goal split and their players' goals may change; every other row is unchanged, which the
  before/after comparison against prod shows model by model before merge.

decisions_taken: >
  One goal definition in base_apif__fixture_events, read by the base models and tests that count
  goals; the nameless-event rule as #176's findings state it; negative minutes as shoot-out kicks;
  the award's kind and on-pitch score carried to fct_fixture: approved in chat, 2026-10-11.
  Measured on prod before the plan: leaving out every goal event without a scorer id would break
  275 matches that add up today, so the nameless rule applies only where the match then adds up;
  negative minutes fix 5 matches and break none.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; columns on existing models. RECURRING COST: the
  changed models' nightly read, measured by dry-run against prod before merge.

decisions_reserved:
  - The goals list and goal-data state on mart_competition_fixtures, and the hand goal corrections seed (#176, the next MR).
  - The page (#175).

done_when:
  - dbt parse passes; sqlfluff shows no new finding on every changed model and test.
  - The changed base and core models' compiled SQL against prod differs from today's tables only on the matches the cleaning fixes.
  - The changed tests' compiled SQL against prod returns no rows.
  - pytest tests/ passes; the offline CI gates pass; data:build:mr is green on the MR.

amendments: >
  none
