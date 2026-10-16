# Task contract — the played match's missing data: shoot-out, winner, score after each goal, line-up order

objective: >
  The played match page needs four values the warehouse does not serve. mart_competition_fixtures
  gains the shoot-out score (shootout_home, shootout_away) and the team that won or went through
  (winner_team_sk); each entry of its goals list gains the score after that goal
  (score_home_after, score_away_after); mart_player_fixture_stats gains a player's place on the
  team sheet (lineup_order). No page and no payload the site reads changes.

refs: >
  #175, the played match page (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/175);
  #178 step 1, the shoot-out score and the team that went through
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/178).
  The plan, the column names and the order rule in decisions_taken: approved in chat, 2026-10-15.

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__fixtures_next.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/fct_fixture_lineup.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_mart_competition_fixtures_goals_add_up.sql
  - dbt_project/tests/assert_fixture_lineup_order_starters_first.sql
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_result_corrections_applied.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: stg_apif__fixtures_next reads RAW_APIF_FIXTURES_NEXT; base_apif__lineups reads
  stg_apif__lineups and the seed fixture_lineup_corrections. dbt is the only writer of every model
  in scope.
  downstream: pasted output of `dbt ls --resource-type model --select stg_apif__fixtures_next+
  base_apif__lineups+ --output name` on the branch's base (68 models, the wide fan-out of
  base_apif__fixtures_next): base_apif__fixture_events base_apif__fixture_players
  base_apif__fixture_statistics base_apif__fixtures_next base_apif__lineups base_apif__players
  base_apif__teams base_apif__teams_global dim_player dim_player_team_season_mapping dim_team
  dim_team_competition_season_mapping fct_fixture fct_fixture_event fct_fixture_lineup
  fct_fixture_player_stats fct_fixture_team_stats int_legs__player_match
  int_legs__team_from_players int_legs__team_match int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_match__metrics int_player_momentum__metrics int_player_profile__contribution
  int_player_profile__yoy int_player_season__metrics int_player_season__team
  int_player_season_position__metrics int_player_season_record
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season_record mart_competition_fixtures
  mart_competition_index mart_competition_season_summary mart_fixture_standing_context
  mart_head_to_head mart_leaderboards mart_match_days mart_matchday_insights mart_next_matchday
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats
  mart_player_momentum mart_player_profile mart_player_season_record mart_roster mart_standings
  mart_team_competition_benchmarks mart_team_fixtures mart_team_leaderboards
  mart_team_market_value mart_team_momentum_window mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record mart_team_window_metrics
  stg_apif__fixtures_next. Only columns are added. The star selects of the changed models
  (fct_fixture in int_legs__team_match, int_legs__player_match and mart_competition_index;
  base_apif__lineups in fct_fixture_lineup) feed CTEs whose outputs name their columns, except
  fct_fixture_lineup, which gains lineup_order by design. scripts/export_site_data.py names the
  columns it reads from mart_competition_fixtures and mart_player_fixture_stats, so no payload
  gains a key.
  layer_rules: extraction in staging; the winner and the order are first logic in base; core casts
  and passes through; marts serve. No new model; check_layer_contract unchanged.
  deploy_order: additive columns; the 04:00 nightly builds them after merge; no reader exists
  until the page MR.
  blast_radius: three marts and their parents gain columns; every existing column and row of
  every model is unchanged, compared on prod data before merge.

decisions_taken: >
  Approved in chat, 2026-10-15: the warehouse MR comes before the page; the column names
  shootout_home, shootout_away, winner_team_sk, goals.score_home_after, goals.score_away_after and
  lineup_order. winner_team_sk is the team that won or went through: the awarded team on an awarded
  result, otherwise the shoot-out's winner on a match settled on penalties, otherwise the side
  with more goals; NULL on a draw and on a match not played. The score after each goal is served
  on every goal entry of a list in match order and is NULL on a per-scorer entry. lineup_order:
  starters first, then substitutes; a provider sheet in the provider's order; a researched sheet's
  starters by pitch position (grid row, then column), its substitutes and any starter without a
  position by shirt number.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; columns on existing models. RECURRING COST: the
  staging read of RAW_APIF_FIXTURES_NEXT gains two JSON paths; measured by dry-run before and
  after and put to the CPO in GiB.

decisions_reserved:
  - A match settled on penalties still counts as a draw in int_legs__team_match (results, form,
    standings); #178 and #179 own that, not this task.
  - Matches played then awarded (status AWD) stay out of mart_player_fixture_stats and the match
    window and boards.
  - How the site's match rows show a shoot-out (#178 steps 2-3).

done_when:
  - dbt parse and compile pass; sqlfluff lint of every changed model is clean against main's baseline; check_layer_contract, check_description_hygiene and the governance gates pass; the full pytest suite passes.
  - data:build:mr is green, its tests included.
  - On prod data, from the MR build, every changed mart equals prod on every key and every existing column; the new columns are counted (PEN matches with a shoot-out score and a winner; played matches with a winner; goal entries with a score after; sheet rows with an order).
  - The warehouse read of stg_apif__fixtures_next before and after is measured and put to the CPO in GiB.

amendments: >
  + dbt_project/tests/assert_fixture_lineup_order_starters_first.sql. Authority: the standing rule
  engineering_standards.md §3.1 (a derived column carries a consistency test), raised by the
  analytics engineer in review round 1. Content: lineup_order numbers each team sheet 1 to n with
  every starter before every substitute.
  + dbt_project/seeds/fixture_result_corrections.csv, dbt_project/seeds/schema.yml,
  dbt_project/tests/assert_result_corrections_applied.sql. Authority: approved in chat,
  2026-10-16, after data:build:mr found 30 matches settled on penalties without a shoot-out score
  from the provider. Content: the seed gains shootout_home and shootout_away, the official
  shoot-out score, researched and sourced for those 30 matches; base applies them over the
  provider's and keeps the provider's beside them; the seed's test checks they are applied and
  still needed. The PEN tests stay errors, so a new case turns the nightly red until it has a
  researched row.
