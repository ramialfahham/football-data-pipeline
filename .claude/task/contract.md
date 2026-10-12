# Task contract — a played match's goals on the match mart

objective: >
  mart_competition_fixtures serves every played match's goals as one list and one goal-data
  state: goals (every goal with its minute; a 0-0 has none), goals_without_minutes,
  not_recorded, or awarded; with the award's kind and the score on the pitch. The goals come from
  the goal events where they add up to the score, otherwise from the players' goals with the
  own-goal events. A new seed, fixture_goal_corrections, holds each goal of a match the provider's
  data gets wrong, researched and sourced; base_apif__fixture_events counts those goals instead of
  the provider's, so every reader sees the same goals.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the goals,
  step 2. The plan: approved in chat, 2026-10-11.

scope_paths:
  - dbt_project/seeds/fixture_goal_corrections.csv
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_result_corrections_applied.sql
  - dbt_project/tests/assert_fixture_events_only_from_latest_fetch.sql
  - dbt_project/tests/assert_mart_competition_fixtures_goals_add_up.sql
  - dbt_project/tests/assert_player_row_and_events_same_team.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt seed loads fixture_goal_corrections, which base_apif__fixture_events applies, and
  fixture_result_corrections, which base_apif__fixtures_next applies. Nothing else writes a goal,
  a score or a result.
  downstream: `dbt ls --select fixture_result_corrections+ fixture_goal_corrections+
  --resource-type model` on the branch gives 67 models: base_apif__fixture_events
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
  layer_rules: the seeds are configuration applied in base; core serves the events and the
  fixtures; the goals list and the state are consumption, on the existing match mart. No new model.
  deploy_order: one dbt run; dbt seed precedes the models in data:build:main and fdp-nightly.
  blast_radius: the 42 matches in fixture_goal_corrections: their goal events, and their team
  goal split and players' goals where those read the events. The 43 new rows of
  fixture_result_corrections: 20 scores change (all after extra time, no winner changes), 8
  walkovers the provider files 0-0 gain their winner (a draw becomes a win and a loss in every
  results model above int_legs__team_match), 11 statuses change from WO to AWD, and 23 awards gain
  their kind. Every goals, results and form model in the list above that reads these matches
  changes with them; the standings come from the provider's tables and do not. The new columns of
  mart_competition_fixtures.

decisions_taken: >
  The goals list and goal-data state on mart_competition_fixtures, no new mart; the seed applied
  in base_apif__fixture_events; each seeded match researched with an official record or two
  sources on different sites naming its scorers: approved in chat, 2026-10-11. A researched
  match's sourced goals come before the players' goals, because they carry minutes. The provider's
  goal events of a seeded match stay in the events, not counted. A played match whose goal events
  exist but add up neither alone nor with the players' goals fails a test until it has a seed row,
  so not_recorded means the provider recorded no goals. The choice of a match's goal source and its
  state live in mart_competition_fixtures, with no intermediate model (the CPO's choice of the
  match mart, approved in chat, 2026-10-11); its players' fallback reads
  fct_fixture_player_stats.goals, the players' goals base_apif__fixture_players already chose,
  so no rule is restated.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; a correction seed on the existing pattern, columns
  on existing models. RECURRING COST: the changed models' nightly read, measured by dry-run against
  prod before merge.

decisions_reserved:
  - The page and the played-match export (#175).
  - The wrong team in CAF match 1619054.
  - The seven mart renames.

done_when:
  - dbt parse passes; sqlfluff shows no new finding on every changed model and test.
  - Every seed row passes a local check: sides add up to the score, sources official or two sites.
  - The changed models' compiled SQL against prod gives every played match one state, and the new and changed tests return no rows.
  - pytest tests/ passes; the offline CI gates pass; data:build:mr is green on the MR.

amendments: >
  fixture_result_corrections joins the scope, approved in chat, 2026-10-11. The new goals test
  found 23 matches the provider itself files as awarded (WO or AWD) with no record of how the
  award came about; each researched one gets a sourced row with its kind, as the 44 awarded rows
  before. The research of the matches whose goal events do not add up found 20 whose stored score
  is the two-leg aggregate or counts shoot-out kicks; each gets a sourced row with the score after
  extra time, as the extra-time rows before. assert_result_corrections_applied no longer calls an
  award "no longer needed": the provider never says how an award came about.
  data:build:mr failed on assert_player_row_and_events_same_team in one match, the 2019 Copa
  Libertadores final (247587): the provider files both teams' players under the other team, in its
  player rows and its events alike, so the corrected goals disagree with its player rows. The test
  now compares only the provider's own events with the player rows, as
  assert_fixture_events_only_from_latest_fetch does; the swapped team lists of that match are a
  separate item. Approved in chat, 2026-10-11, with a fourth review round.
