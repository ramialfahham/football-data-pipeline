# Task contract — awarded results carry their kind and the score on the pitch

objective: >
  fixture_result_corrections records how each awarded result came about: not played, played, or
  abandoned, with the score on the pitch for the last two. The 44 matches researched for #176
  get a sourced row: 42 never played and awarded, one played and awarded afterwards, one whose
  provider score is wrong. The seed's test fails a row whose kind and on-pitch score do not fit
  its award.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): every played
  match has one goal-data state, among them an awarded result with its kind, approved in chat,
  2026-10-11. This change: approved in chat, 2026-10-11.

scope_paths:
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_result_corrections_applied.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt seed loads fixture_result_corrections; base_apif__fixtures_next applies each row's
  official score, status and winner and keeps the provider's beside them. The three new columns
  have no reader yet. Nothing else writes the result.
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
  assert_result_corrections_applied, checks every row is applied, sourced and valid.
  layer_rules: a seed is configuration; no model changes. An awarded result (status AWD) already
  counts in results and tables and stays out of form and stat windows (int_legs__team_match).
  deploy_order: one dbt run; dbt seed precedes the models in data:build:main and fdp-nightly.
  blast_radius: 43 matches the provider files as played become awarded (status AWD): 28 Super Lig
  2022 matches after the withdrawals of Gaziantep FK and Hatayspor, 14 other forfeits and
  Verona-Roma 2020. Two scores change: Etoile Matoury-Le Geldar 2-2 becomes 1-1, and La
  Passe-Volcan Club 0-1 becomes a win for La Passe with no score set.

decisions_taken: >
  The award's kind (not_played, played, abandoned) and the score on the pitch as seed columns,
  the 9 existing rows filled, and the 44 researched rows, each official or with two match reports
  on different sites: approved in chat, 2026-10-11. A won match with no score set follows the
  existing Bastia-Lyon row: 0-0 with the winner in awarded_to_team_id.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; three columns on an existing seed and one more
  problem kind in its existing test. RECURRING COST: none.

decisions_reserved:
  - Serving the kind and the on-pitch score to the marts and pages, and the goal lists (#176).
  - The header status word of an awarded result (#175).
  - The goal corrections of the 30 played matches researched with these (#176).
  - The wrong team in CAF match 1619054.

done_when:
  - dbt parse passes; sqlfluff on the test shows no finding.
  - Every row passes a local check of the test's rules: kind with award, on-pitch score where it belongs, source shape and sites.
  - pytest tests/ passes; the offline CI gates pass; data:build:mr is green on the MR.

amendments: >
  none
