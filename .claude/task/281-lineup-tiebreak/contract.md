# Task contract — Every build keeps the same lineup row for a player listed twice

objective: >
  Issue #281. Every build reads the same team sheet and the same row for a player the provider
  lists twice in it. The player-row pick in base_apif__lineups already orders by the sheet's grain
  (starters before the bench, then sheet order), which the lineup_sheets grain test holds unique.
  What is left is the pick of a team's fetch in base_apif__lineup_sheets, ordered by its ingest
  time alone: a tie there must fail a test, never be settled by the build.
refs: "#281 (CPO, approved in chat 2026-11-09)"

scope_paths:
  - .claude/task/281-lineup-tiebreak/**
  - dbt_project/models/2_base/api_football/base_apif__lineup_sheets.sql
  - dbt_project/tests/assert_lineup_fetches_never_tie.sql

acceptance_criteria:
  - When the provider lists a player twice in one team sheet, every build keeps the same row, chosen by a stated rule.
  - A player's shirt number, position, grid position and lineup order in a match are the same on every build.
  - A test fails when the rows that pick a player's line in a team sheet have tied order keys.

impact_map: >
  writers: base_apif__lineup_sheets (which fetch of a team's sheet is read); base_apif__lineups
  reads it unchanged.
  downstream: `dbt ls --select base_apif__lineup_sheets+ --resource-type model` → 62 models
  (base_apif__lineups, base_apif__fixture_players_from_lineups, base_apif__players, dim_player,
  fct_fixture_lineup, fct_fixture_player_stats, and the marts mart_competition_fixtures
  mart_leaderboards mart_match_days mart_matchday_insights mart_player_career
  mart_player_competition_benchmarks mart_player_fixture_stats mart_player_index
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_team_competition_benchmarks mart_team_competitions
  mart_team_index mart_team_leaderboards mart_team_momentum_window mart_team_page_window_metrics
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record
  mart_team_window_metrics).
  layer_rules: dedup of fetches is base work (layering.md, 2_base); no new model, no grain change.
  deploy_order: no column, table or grain change.
  blast_radius: none on today's data. Measured on prod 2026-11-15 (read-only, 464 MB in all):
  0 of 126,250 team fetches in stg_apif__lineups share an ingest time with another fetch of the
  same team; 0 of 115,187 latest team sheets are tied; 134 players are listed twice in one sheet
  of base_apif__lineup_sheets (83 across the eleven and the bench, 51 in one list), and none of
  them has a tied (is_starter, sheet_index).

decisions_taken: >
  CPO, approved in chat 2026-11-09 (#281). The rule for a player listed twice is the stated one in
  cleaning_rules.md: he keeps his first listing, the starters before the bench, then the sheet's
  order; it is unchanged, and the lineup_sheets grain test (league_code, fixture_id, team_id,
  is_starter, sheet_index) is the test that fails on tied order keys for that pick.
  Engineering: the fetch pick keeps every fetch at the latest ingest time (rank, not row_number),
  so a tie gives two sheets and the grain test fails; the new singular test fails on any two
  fetches of one team at one ingest time, which also covers the earlier fetch that lends grid
  places. Neither picks between tied fetches, because nothing in the data says which is newer.
  Thresholds: no new mechanism. Recurring cost: one test over stg_apif__lineups, about 0.11 GB a
  build (dry run 106 MB).

decisions_reserved:
  - none: the rule is the stated cleaning rule; a tie, should one appear, fails the build and goes
    to the CPO with the rows.

done_when:
  - dbt parse passes; sqlfluff lint clean on the changed files; layer contract and description hygiene pass
  - full pytest passes
  - data:build:mr is green with the grain test and the new test passing
  - the MR's fct_fixture_lineup equals prod's on shirt_number, position_code, grid_position and
    lineup_order for every row read from the same fetch

amendments: (none)
