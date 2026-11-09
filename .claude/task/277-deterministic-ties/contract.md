# Task contract — every build picks the same row: deterministic tie-breaks

objective: >
  Issue #277: every row a model picks among several is picked by a stated rule, and no model or
  test uses any_value or approx_quantiles, so two builds of the same data give the same output.
  A CI check bans both functions; tests pin each one-value-per-group assumption and each order.

refs: >
  #277, plan and rules ruled by the coordinating session on 2026-11-09 (correctness fixes picking
  the right row where today's pick is arbitrary). Found by the prod comparison for #83 (!403).

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__standings.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__standings.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_standings.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_standings__official_rank.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__standings_primary.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_legs__team_from_players.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_squad_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__streaks.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_team_competitions.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_competition_index.sql
  - dbt_project/models/5_marts/shared/mart_competition_season_summary.sql
  - dbt_project/models/5_marts/shared/mart_player_window_metrics.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_lineup_researched_matches_hold.sql
  - dbt_project/tests/assert_player_shares_name_at_club.sql
  - dbt_project/tests/assert_result_corrections_applied.sql
  - dbt_project/tests/assert_team_form_window_follows_the_rule.sql
  - dbt_project/tests/assert_card_events_name_one_team_per_player.sql
  - dbt_project/tests/assert_team_benchmark_rank_follows_direction.sql
  - dbt_project/tests/assert_player_position_follows_the_rule.sql
  - dbt_project/tests/assert_cup_status_follows_the_reached_tie.sql
  - dbt_project/macros/one_value.sql
  - dbt_project/docs/engineering_standards.md
  - dbt_project/docs/layering.md
  - scripts/check_layer_contract.py
  - tests/test_check_layer_contract.py
  - tests/test_one_value_macro.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/277-deterministic-ties/contract.md
  - .claude/task/277-deterministic-ties/review.md
  - .claude/task/277-deterministic-ties/review_input.patch

impact_map: >
  writers: dbt only; no ingestion change. stg_apif__standings gains standing_section_order, the
  section's position in the provider's standings list for that season; it flows through
  base_apif__standings and fct_standings. Every other change rewrites how an existing column is
  picked or aggregated; no grain changes.
  lineage: `dbt ls --resource-type model --select stg_apif__standings+ base_apif__fixture_events+
  int_player_momentum__metrics+ int_player_season_record+ int_player_competition_benchmarks+
  int_team_competition_benchmarks+ int_legs__team_from_players+ int_player_profile__contribution+
  int_player_squad_window__metrics+ int_team_profile__streaks+ mart_player_profile+
  mart_leaderboards+ mart_team_leaderboards+ mart_team_competitions+ mart_competition_fixtures+
  mart_competition_index+ mart_competition_season_summary+ mart_player_window_metrics+` returns 86
  models: base_apif__fixture_events base_apif__fixture_players
  base_apif__fixture_players_from_lineups base_apif__fixture_statistics base_apif__lineups
  base_apif__players base_apif__standings base_apif__teams base_apif__teams_global dim_player
  dim_player_team_season_mapping dim_team fct_fixture_event fct_fixture_lineup
  fct_fixture_player_stats fct_fixture_team_stats fct_standings int_legs__player_match
  int_legs__team_from_players int_legs__team_match int_player__page_profile
  int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_match__metrics int_player_momentum__metrics
  int_player_page__window_seasons int_player_profile__contribution int_player_profile__yoy
  int_player_season__metrics int_player_season__team int_player_season_position__metrics
  int_player_season_record int_player_squad_window__metrics int_player_window__metrics
  int_standings__official_rank int_standings__section_kinds int_team__current_national_competitions
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__biggest_results int_team_season__deserved_vs_actual
  int_team_season__longest_runs int_team_season__metrics int_team_season__metrics_cumulative
  int_team_season__standings_primary int_team_season__table_by_time int_team_season__table_legs
  int_team_season__table_state int_team_season_record mart_competition_fixtures
  mart_competition_index mart_competition_season_summary mart_fixture_standing_context
  mart_head_to_head mart_leaderboards mart_match_days mart_matchday_insights mart_next_matchday
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_competitions mart_team_fixtures mart_team_index mart_team_leaderboards
  mart_team_market_value mart_team_momentum_window mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record mart_team_window_metrics stg_apif__standings.
  consumption: no export change; the export reads the same columns.
  ci_layer_rules: scripts/check_layer_contract.py (gains the any_value / approx_quantiles ban),
  scripts/check_description_hygiene.py, scripts/check_relationships_coverage.py.
  deploy_order: one merge; the nightly rebuilds every model. No backfill.
  blast_radius: values change only where today's pick is arbitrary. Measured in prod: 323
  team-seasons with tied standings rows (rank and form of the latest table); 37,394 of 239,216
  player-seasons with more than one position, 4,085 with a tied modal position; 10 team-board and
  some player-board rows whose board order is a tie across seasons; benchmark quartiles where
  approx_quantiles was off and peer means by at most 2.1e-14; 37 team-rounds with two knockout
  ties under one round name. Every other changed column replaces any_value by min or max over a
  group that holds one value, so it does not change. Exact differences come from the MR build
  compared with prod.

approved_design:
  - none: no page output changes

decisions_taken: >
  The rules, ruled by the coordinating session on 2026-11-09 as correctness fixes: standings take
  the latest load, then the provider's section order; position is the most frequent in the
  group, then the most recent match's, then the code; board_leader_order ends with
  season_api_year descending, then league_code, in both leaderboard marts; peer and league means
  are exact (bignumeric) and quartiles exact with percentile_disc, the exact form of the same
  definition approx_quantiles approximated (measured equal on 14,942 of 15,029 medians, where
  percentile_cont is equal on 8,777); a reached knockout round names the tie that contains the
  reached fixture, joined on its opponent, else the latest tie; the previous round's tie is the
  latest tie under that round name. The ban extends the existing check_layer_contract.py. The one
  new mechanism is the one_value macro (amendment 1); no recurring cost.

decisions_reserved:
  - The round-names fault itself (#278).

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
  - python scripts/check_layer_contract.py passes, and fails on a planted any_value (pytest).
  - python -m pytest tests -q is green.
  - SQLFluff adds no violation on any changed model.
  - The benchmark models' slot time is measured against the 300 s limit.
  - CI's data:build:mr is green; every changed model and everything downstream is compared with prod both ways, and every difference is listed.

amendments:
  - 2026-11-09: + dbt_project/macros/one_value.sql, tests/test_one_value_macro.py — authority: approved in chat, 2026-11-09 (a new mechanism); content: one_value(column) returns min(column) and fails the build with error() when a group holds two values, used at every model site where any_value held one value per group.
  - 2026-11-09: + dbt_project/docs/engineering_standards.md, dbt_project/docs/layering.md — authority: approved in chat, 2026-11-09, word for word; content: the ban's rule line in engineering_standards.md §1.1, and any_value dropped from layering.md's staging example.
  - 2026-11-09: + dbt_project/tests/assert_player_position_follows_the_rule.sql, dbt_project/tests/assert_cup_status_follows_the_reached_tie.sql — authority: acceptance criteria 2 and 5 (test with the change); content: a data test per new rule, each failing when a picked position or tie is one the rule does not pick.
