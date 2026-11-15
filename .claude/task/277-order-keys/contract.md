# Task contract — every picked row has unique order keys

objective: >
  Issue #277, the last open line: every row a model picks by an order is picked from order keys
  that are unique within the group, and a test or the SQL itself proves it. !411 and !414 built the
  other seven lines and the first four picks; an audit of every pick site in the models found 31
  sites where two rows can still tie.

refs: >
  #277 (plan approved in chat, 2026-11-09). Follows !411 and !414. Audit of every row_number,
  array_agg ... limit, first_value and last_value site under dbt_project/models.

scope_paths:
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__coach_career.sql
  - dbt_project/models/2_base/api_football/base_apif__competition_seasons.sql
  - dbt_project/models/2_base/api_football/base_apif__league_entity.sql
  - dbt_project/models/2_base/api_football/base_apif__transfers.sql
  - dbt_project/models/2_base/api_football/base_apif__teams.sql
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team__current_national_competitions.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_player__page_profile.sql
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - .claude/task/277-order-keys/contract.md
  - .claude/task/277-order-keys/review.md
  - .claude/task/277-order-keys/review_input.patch

impact_map: >
  writers: dbt only; no ingestion, seed or export change. Each changed model keeps its grain and
  columns; only the order of a pick gains final keys, one CTE in base_apif__fixture_statistics
  carries the provider's team id to order by it, and base_apif__lineups' club_on_match_day reads
  the same day's departures.
  lineage: `dbt ls --resource-type model --output name --select base_apif__coach_career+
  base_apif__competition_seasons+ base_apif__league_entity+ base_apif__transfers+
  base_apif__teams+ base_apif__teams_global+ base_apif__fixture_statistics+ base_apif__lineups+
  int_team_momentum_window+ int_team__current_national_competitions+ int_player_season_record+
  int_player__page_profile+ mart_matchday_insights+ mart_competition_fixtures+
  mart_player_competition_benchmarks+` returns 99 models: base_apif__coach_career
  base_apif__competition_seasons base_apif__fixture_players base_apif__fixture_players_from_lineups
  base_apif__fixture_statistics base_apif__league_entity base_apif__lineup_sheets base_apif__lineups
  base_apif__players base_apif__teams base_apif__teams_global base_apif__transfers
  dim_coach_team_mapping dim_competition_season dim_league dim_player
  dim_player_team_season_mapping dim_team fct_fixture_lineup fct_fixture_player_stats
  fct_fixture_team_stats fct_standings fct_transfer int_competition_season__club_windows
  int_competition_season__player_stat_corrections int_legs__player_match int_legs__team_from_players int_legs__team_match
  int_player__national_team_minutes int_player__page_profile int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_match__metrics int_player_momentum__metrics int_player_page__window_seasons
  int_player_profile__contribution int_player_profile__yoy int_player_season__metrics
  int_player_season__team int_player_season_position__metrics int_player_season_record
  int_player_squad_window__metrics int_player_window__metrics int_standings__official_rank
  int_standings__section_kinds int_team__current_national_competitions int_team__featured_season
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_competition_phase__metrics int_team_momentum__metrics int_team_momentum_window
  int_team_profile__streaks int_team_profile__yoy int_team_season__biggest_results
  int_team_season__deserved_vs_actual int_team_season__longest_runs int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season__standings_primary
  int_team_season__table_by_time int_team_season__table_legs int_team_season__table_state
  int_team_season_record int_team_window__metrics mart_competition_fixtures mart_competition_index
  mart_competition_season_summary mart_fixture_standing_context mart_head_to_head
  mart_leaderboards mart_match_days mart_matchday_insights mart_next_matchday mart_player_career
  mart_player_competition_benchmarks mart_player_fixture_stats mart_player_index
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_competitions mart_team_fixtures mart_team_index mart_team_leaderboards
  mart_team_market_value mart_team_momentum_window mart_team_page_window_metrics
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record
  mart_team_window_metrics.
  base_apif__lineup_sheets is rebuilt downstream of base_apif__teams and base_apif__transfers; its
  file does not change.
  consumption: no export change; the export reads the same columns.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py,
  scripts/check_relationships_coverage.py.
  deploy_order: one merge; the nightly rebuilds every model. No backfill. The new source tests run
  first in the nightly `dbt build`; each passes on prod today (measured below).
  blast_radius: values change only where two rows tie today. Measured in prod, read-only: 264
  coach stints whose copies in one load differ in end date or team name; 9 transfers whose copies
  differ in type; 0 ties on the keys the new tests pin (raw loads, stg events, line-ups,
  standings, teams, leagues, dim_competition_season); 3,525 player-dates with moves to two clubs on
  one day, 1,223 of them settled by the club not left again that day, the rest giving no club, which
  changes the placement of 2 line-up sheets against a lowest-id pick. Ties in team names, form-window legs, goal
  lists, the next round and the competition order are counted from the MR build against prod.
  recurring_cost: the 12 new tests scan 32.5 MB a night (dry run), at most 120 MB with the 10 MB
  per-query billing minimum.

approved_design:
  - none: no page output changes

decisions_taken: >
  The rule, under the approved #277 line "every row picked by an order holds a test that the order
  keys are unique within the group": each pick's order ends with keys that make it total in its
  input, proven by a GROUP BY key, a tested unique key, or a new uniqueness test on the input.
  Where tied rows hold the same value today and the input is unique on the order keys, a test pins
  it: the six raw tables on (league_code, ingested_at); stg_apif__fixture_events, stg_apif__lineups,
  stg_apif__standings, stg_apif__teams and stg_apif__leagues on each pick's partition and order
  keys; dim_competition_season on (league_code, season_api_year). Where rows tie in real data, the
  order gains final keys: a coach stint takes the open or latest end date, then the team name; a
  transfer takes a named type before '-' and null, then the type; a team name takes the newer season
  or the later fixture, then the name; the base_apif__league entity, competition-season and global
  team picks end with league_code, completing their tested key; a fixture's team statistics take the
  line the provider filed under the correct team id, then the provider id; a form-window leg ends
  with its fixture; a nation's current competition, a player's featured season and a player's
  competition order end with season_sk; the next round ends with fixture_sk; a goal list ends with
  team, own goal and player; a player's position to date takes the most frequent, then the latest
  match by kickoff time, then the code; a player's club on the match day takes the latest move, then
  the club the player does not leave again that day, and two clubs still tied give no club, because
  the source does not say which one. No new mechanism: every test is dbt_utils
  unique_combination_of_columns, already in use.

decisions_reserved:
  - none: every pick follows the #277 rule; no metric, label or page composition changes.

acceptance_criteria:
  - A team's primary standings row is the one the source itself marks as latest, by a stated rule, so its rank and form are the same on every build.
  - A player's position for a season or a form window is chosen by a stated rule, the same on every build.
  - A league leader's place on a team board is fixed when the same team leads with the same value in two seasons.
  - Peer means and quartiles in the player and team benchmarks are exact and the same on every build.
  - A team's reached knockout round names the tie that contains its reached fixture.
  - No model or test uses any_value or approx_quantiles, and CI fails a new use.
  - Where a column replaced by min() or max() holds one value per group, a test fails if it ever holds two.
  - Every row picked by an order holds a test that the order keys are unique within the group.

done_when:
  - dbt parse succeeds from the repo root.
  - python scripts/check_layer_contract.py passes.
  - python -m pytest tests -q is green.
  - SQLFluff adds no violation on any changed model.
  - CI's data:build:mr is green; every changed model and everything downstream is compared with prod, and every difference is listed in the MR.

amendments:
  - 2026-11-15: + dbt_project/models/2_base/api_football/base_apif__lineups.sql — authority: the #277 acceptance line "every row picked by an order holds a test that the order keys are unique within the group" (plan approved in chat, 2026-11-09); the file was held back only while #281 (!441) edited it, and the coordinating session released it on 2026-11-15 for this one pick once !441 is in main; content: the club_on_match_day pick, which orders a player's transfers by date alone, takes the club not left again that day, and two clubs still tied give no club. No other CTE of the file changes.
