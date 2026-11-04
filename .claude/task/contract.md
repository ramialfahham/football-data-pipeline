# Task contract — fill a goalkeeper's blank goals against

objective: >
  Issue #247: a goalkeeper's blank goals against takes the team's goals conceded when the keeper
  played the whole match alone, and the goals conceded between the minute on and off when the
  keeper came on or went off; where neither can be read it stays blank and is never counted as 0.

refs: >
  #247, approved in chat, 2026-11-03; its plan approved in chat, 2026-11-04.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/models/docs/cleaning_rules.md
  - .claude/task/**

impact_map: >
  writers: base_apif__fixture_players is written by dbt only; it reads stg_apif__fixture_players,
  base_apif__fixtures_next, base_apif__fixture_events and base_apif__fixture_statistics, all
  unchanged.
  downstream: `dbt ls --select base_apif__fixture_players+ --resource-type model` lists 48 models:
  base_apif__lineups, base_apif__players, dim_player, fct_fixture_lineup, fct_fixture_player_stats,
  int_legs__player_match, int_legs__team_from_players, int_player_club_season__metrics,
  int_player_competition_benchmark_metrics_long, int_player_competition_benchmarks,
  int_player_match__metrics, int_player_momentum__metrics, int_player_profile__contribution,
  int_player_profile__yoy, int_player_season__metrics, int_player_season__team,
  int_player_season_position__metrics, int_player_season_record,
  int_team_competition_benchmark_metrics_long, int_team_competition_benchmarks,
  int_team_momentum__metrics, int_team_profile__yoy, int_team_season__deserved_vs_actual,
  int_team_season__metrics, int_team_season__metrics_cumulative, int_team_season_record,
  mart_competition_fixtures, mart_leaderboards, mart_match_days, mart_matchday_insights,
  mart_player_career, mart_player_competition_benchmarks, mart_player_fixture_stats,
  mart_player_momentum, mart_player_profile, mart_player_season_record, mart_roster,
  mart_team_competition_benchmarks, mart_team_competitions, mart_team_index,
  mart_team_leaderboards, mart_team_momentum_window, mart_team_profile, mart_team_season,
  mart_team_season_insights, mart_team_season_record, mart_team_window_metrics. Only the player
  chain reads the column: fct_fixture_player_stats, int_legs__player_match,
  int_player_club_season__metrics, int_player_momentum__metrics, int_player_season_record,
  mart_player_fixture_stats (grep of `goals_against` over dbt_project/models/*player*).
  layer_rules: base holds cleaning (dbt_project/docs/layering.md); check_layer_contract applies; no
  new model, no partition or cluster key.
  deploy_order: no column added or removed, so nothing downstream breaks before the merge; the
  values change at the first nightly after the merge.
  blast_radius: goalkeeper goals against, saves percentage and the goalkeeper benchmarks change
  where a blank is filled or a wrong 0 goes; 2026 BL1, UCL and UNL hold 141 blank lines. Outfield
  players and team numbers are unchanged.

approved_design:
  - none: no page output changes

decisions_taken: >
  The issue's rules, as approved. A goalkeeper's blank is a zero only without minutes or when the
  team conceded none. The minute on and off come from the keeper's substitution event (player went
  off, assist came on; `is_substitute` is false for both keepers) or a card other than a yellow
  card. A goal in the same minute as the change leaves the value blank. No new mechanism and no
  recurring cost.

decisions_reserved:
  - none: the rules are the approved issue's; any line left blank is reported to the CPO, not forced

done_when:
  - dbt parse passes and SQLFluff reports nothing new on the model
  - the answer-key and cleaned tests pass in data:build:mr
  - the 2026 count of blank lines in BL1, UCL and UNL is reported from the MR's dataset, each remaining blank with its reason
  - the 437 lines with a provider value at 90 minutes are unchanged

amendments: (none)
