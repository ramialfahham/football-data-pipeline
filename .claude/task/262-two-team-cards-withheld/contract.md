# Task contract - a player whose card events name two teams has his cards withheld and listed, not a build error

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." When the
  card events of one player in one match name two teams, base_apif__fixture_players and
  base_apif__fixture_player_lines call one_value('team_id') on his cards, which raises error() and
  fails the build on a provider input; assert_card_events_name_one_team_per_player also fails at
  error. Now the player's two card counts are blank, as cards_need_research already blanks them,
  on the player-line path and on the line-up path, until sourced research stands in
  fixture_card_corrections; the match is a cards_withheld row of mart_competition_research_list;
  the error-severity test proves both paths withhold, against a set of two-team players it derives
  from the card events, never from the flag. A researched match is settled on both paths.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). Part of the three provider checks that
  move from stopping the nightly to withholding; (d), the player bio conflict, is the first of them.

depends_on:
  - none: every file this change edits is on gitlab/main. The new Python test carries its own render helper, so it does not need the open merge request for the player bio conflict

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/macros/card_events_naming_two_teams.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_player_lines.sql
  - dbt_project/models/5_marts/shared/mart_competition_research_list.sql
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_card_events_name_one_team_per_player.sql
  - dbt_project/tests/assert_two_team_cards_listed.sql
  - dbt_project/tests/assert_two_team_cards_answer_key.sql
  - tests/test_two_team_cards_wiring.py
  - .claude/task/262-two-team-cards-withheld/contract.md
  - .claude/task/262-two-team-cards-withheld/review.md
  - .claude/task/262-two-team-cards-withheld/review_input.patch

impact_map: >
  writers: the three base models and the mart are written by dbt only (no ingestion code, no raw
  table). base_apif__fixture_player_lines is read by base_apif__fixture_players and
  base_apif__fixture_statistics; base_apif__fixture_players by base_apif__fixture_players_checked,
  base_apif__fixture_players_from_lineups, base_apif__lineup_sheets, base_apif__lineups,
  int_competition_season__player_stat_corrections, int_pipeline__corrections_no_longer_needed and
  mart_competition_research_list; base_apif__fixture_players_from_lineups by fct_fixture_player_stats
  and mart_competition_research_list (`dbt ls --select "<model>+1" --exclude <model>
  --resource-type model`). No column is added or renamed, so no reader changes shape; the
  new macro is read by the two player models, the mart and the two tests.
  downstream (`dbt ls --select "<model>+" --resource-type model`, from the repo root with
  `--project-dir dbt_project`, on this branch cut from gitlab/main):
  base_apif__fixture_players (67 models): base_apif__fixture_events_checked base_apif__fixture_players
  base_apif__fixture_players_checked base_apif__fixture_players_from_lineups base_apif__lineup_sheets
  base_apif__lineups base_apif__players dim_player fct_fixture_event fct_fixture_lineup
  fct_fixture_player_stats int_competition_season__player_stat_corrections int_legs__player_match
  int_legs__team_from_players int_pipeline__corrections_no_longer_needed int_player__national_team_minutes
  int_player__page_profile int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_match__metrics int_player_momentum__metrics
  int_player_page__window_seasons int_player_profile__contribution int_player_season__metrics
  int_player_season__team int_player_season_position__metrics int_player_season_record
  int_player_squad_window__metrics int_player_window__metrics int_team__current_national_competitions
  int_team__featured_season int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_competition_phase__metrics int_team_momentum__metrics int_team_season__deserved_vs_actual
  int_team_season__metrics int_team_season__metrics_cumulative int_team_season_record
  int_team_window__metrics mart_competition_fixtures mart_competition_research_list mart_leaderboards
  mart_match_days mart_matchday_insights mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_index mart_player_momentum mart_player_profile
  mart_player_season_record mart_player_squad_benchmarks mart_player_window_metrics mart_roster
  mart_team_competition_benchmarks mart_team_competitions mart_team_index mart_team_leaderboards
  mart_team_momentum_window mart_team_page_window_metrics mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record mart_team_window_metrics.
  base_apif__fixture_players_from_lineups (55 models): a subset of the 67 above (itself
  and the models after fct_fixture_player_stats and mart_competition_research_list in that list).
  base_apif__fixture_player_lines (87 models): the 67 above plus base_apif__fixture_player_lines,
  base_apif__fixture_statistics, fct_fixture_team_stats, int_legs__team_match,
  int_standings__official_rank, int_team_momentum_window, int_team_profile__streaks,
  int_team_season__biggest_results, int_team_season__longest_runs, int_team_season__standings_primary,
  int_team_season__table_by_time, int_team_season__table_legs, int_team_season__table_state,
  mart_competition_index, mart_competition_season_summary, mart_fixture_standing_context,
  mart_head_to_head, mart_next_matchday, mart_standings, mart_team_fixtures.
  mart_competition_research_list: no downstream model.
  Tests downstream: 519, 478, 665 and 12 (`--resource-type test`). The two that read the changed
  models directly and change here are assert_card_events_name_one_team_per_player (rewritten) and
  the two new ones.
  layer_rules: the withholding is cleaning and sits in base; the list is a mart that reads base, as
  it does now; check_layer_contract applies unchanged: no new model, no materialisation change, no
  per-competition file.
  deploy_order: one build; the nightly picks it up after merge. A rule with no failing input changes
  no value.
  blast_radius: measured read-only on prod before the build: 0 players whose card events name two
  teams (29.7 MB scanned), so no published value changes today. The MR states the same measure on
  its ci_mr tables.

approved_design:
  - none: no page output changes; a withheld card count is blank, as the cards_need_research ones are

decisions_taken: >
  The smallest unit that is wrong is withheld: the player's two card counts (#262, approved in chat,
  15 Nov 2026). The test that caught a provider input stays at error severity and proves the value
  is withheld; no test gets a where exemption, a lower severity or a filter that hides rows. The
  only exemption in the rewritten test and in the listing test is a researched match, whose cards
  the research settles on both paths, which is how cards_need_research already works. The set of
  two-team players is derived from the card events by the macro in the tests, not read from the
  flag. The mart lists a researched match no more, as cards_need_research does not. The ownerless
  card check of base_apif__fixture_players reads one row per team and player
  (player_card_teams), so a player whose cards name two teams is checked under both teams; the
  stat-line player_cards drops its team_id, which nothing else reads. base_apif__fixture_player_lines
  drops its team_id too, which nothing reads.

decisions_reserved: >
  none: how a withheld value looks on a page is the existing withheld-value form; no page, metric,
  name or rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes and sqlfluff lint passes on every changed model and macro
  - python -m pytest tests/test_two_team_cards_wiring.py passes, and fails with the tt join or the researched exemption removed from a model
  - the MR pipeline is green, data:build:mr included

amendments: (none)
