# Task contract — four player pairs with one page title: one person or two

objective: >
  Issue 295. Four pairs of player pages carry one title. Each pair was researched from sourced
  records. Three are one person under two provider ids: Courtney Clarke (421227 into 284468),
  Abdoul Karim Traoré (387805 into 335155) and Sadat Seidu (531305 into 525644), merged by alias
  rows of player_id_overrides, with the checked birth date and nationality in player_bio_corrections.
  Alhassane Bangoura is two people: 51294 is Lass Bangoura (born 1992, Rayo Vallecano), and the
  provider files the 2004-born MC Alger midfielder's 2025 matches and season under 51294 as well.
  Those five matches and the one season row move to 586701, his own id. A new test fails when two
  player pages share every part of their title.

refs: >
  Issue 295; go-live gate issue 290. The cleaning rule "no two people under one id" and the
  player_id_overrides seed: issue 260. Route set by the coordinating session.

scope_paths:
  - .claude/task/295-player-pairs/contract.md
  - .claude/task/295-player-pairs/review.md
  - .claude/task/295-player-pairs/review_input.patch
  - dbt_project/seeds/player_id_overrides.csv
  - dbt_project/seeds/player_bio_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/macros/player_id_override.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base_apif__player_team_season.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_own_player_ids.sql
  - dbt_project/tests/assert_player_page_titles_distinct.sql

approved_design:
  - none: no page output changes beyond the four pairs' pages, their matches and the Guinea events

depends_on:
  - none: needs no open MR's code; it changes seeds, base models and tests on main

shared_files:
  - none: no design baseline, chart manifest or chart pin changes

impact_map: >
  writers: player_id_overrides is read by the player_id_override and fixture_player_id macros in
  base_apif__fixture_events, base_apif__fixture_players, base_apif__lineup_sheets,
  base_apif__players, base_apif__player_profiles, base_apif__player_team_season, base_apif__squads
  and base_apif__transfers. Tests reading the seed directly: assert_own_player_ids,
  assert_player_id_overrides_merged, assert_sheet_and_stats_player_join_on_shirt. Tests re-keying
  staging rows through the macros: assert_base_player_stats_cleaned (moved here from the alias-only
  macro to fixture_player_id, as base_apif__fixture_players keys the same rows),
  assert_fixture_players_from_every_fetch and assert_fixture_players_results_follow_events (already
  fixture_player_id), assert_lineup_two_people_one_id_not_held (alias only; it groups one sheet's
  names by id, which a move between two ids in one match leaves unchanged).
  player_bio_corrections is read by base_apif__players and base_apif__player_profiles, and by
  assert_player_bio_conflicts_settled and assert_identity_fields_never_blanked.
  downstream: `dbt ls --select "player_id_overrides+ player_bio_corrections+" --resource-type model
  --output name` (main 5db6166e), 91 models: base_apif__fixture_events base_apif__fixture_players
  base_apif__fixture_players_from_lineups base_apif__fixture_statistics base_apif__lineup_sheets
  base_apif__lineups base_apif__player_profiles base_apif__player_team_season base_apif__players
  base_apif__squads base_apif__transfers dim_player dim_player_team_season_mapping fct_fixture_event
  fct_fixture_lineup fct_fixture_player_stats fct_fixture_team_stats fct_transfer
  int_competition_season__player_stat_corrections int_legs__player_match int_legs__team_from_players
  int_legs__team_match int_player__national_team_minutes int_player__page_profile
  int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_match__metrics int_player_momentum__metrics
  int_player_page__window_seasons int_player_profile__contribution int_player_profile__yoy
  int_player_season__metrics int_player_season__team int_player_season_position__metrics
  int_player_season_record int_player_squad_window__metrics int_player_window__metrics
  int_standings__official_rank int_team__current_national_competitions int_team__featured_season
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_competition_phase__metrics int_team_momentum__metrics int_team_momentum_window
  int_team_profile__streaks int_team_profile__yoy int_team_season__biggest_results
  int_team_season__deserved_vs_actual int_team_season__longest_runs int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season__standings_primary
  int_team_season__table_by_time int_team_season__table_legs int_team_season__table_state
  int_team_season_record int_team_window__metrics mart_competition_fixtures mart_competition_index
  mart_competition_season_summary mart_fixture_standing_context mart_head_to_head mart_leaderboards
  mart_match_days mart_matchday_insights mart_next_matchday mart_player_career
  mart_player_competition_benchmarks mart_player_fixture_stats mart_player_index
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_competitions mart_team_fixtures mart_team_index mart_team_leaderboards
  mart_team_momentum_window mart_team_page_window_metrics mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record mart_team_window_metrics. The same selection
  holds 1,465 tests, every one of which runs in data:build:mr.
  layer_rules: check_layer_contract.py; the cleaning stays in base, where the seed is applied today;
  the new test reads marts and core only; no partition_by or cluster_by.
  deploy_order: seeds, a macro and base models build together in one run; until the merge the
  deployed tables keep today's ids, and the 04:00 nightly after the merge applies every row.
  blast_radius: eight player ids. The three merged pairs become three pages, each with the matches
  of both ids. 51294 loses five 2025 matches (four Guinea qualifiers, fixtures 1126027, 1126053,
  1126081 and 1126107, and MC Alger's 1485416), one assist (1126027), one yellow card (1126107)
  and the CAFCL 2025 MC Alger season; 586701 gains them. Team totals do not change: every row
  stays with its team. Measured in the MR by comparing ci_mr tables with prod.

decisions_taken: >
  The three merges apply the approved cleaning rule "no two people under one id" with the existing
  alias mode (issue 260). Each keeps the lower id, as all eight earlier merges did. The birth date
  and nationality rows follow the approved player_bio_corrections route, each with its source.
  NEW MECHANISM, approved in chat, 2026-11-16 (the CPO, through the coordinating session): an
  assign_in_fixture row may move a provider id to another provider id within one match, on sheets,
  stat lines and events. A new mode, assign_in_season, moves one /players season row, keyed on
  league, season and team; the seed gains league_code and season_year for it.
  assert_own_player_ids now fails a moving row that is not sourced or that leaves the wrong id in
  its match or season. A moving row names no shirt: the provider's id already names the player in
  that match, and the events carry no shirt. The test that no two player pages share a title is of
  error severity, because two such pages fail the site's SEO audit and block the deploy. No
  recurring cost.

decisions_reserved:
  - none: the one CPO-class question, how to separate the two Bangouras, is answered above

done_when:
  - assert_player_page_titles_distinct returns 0 rows in data:build:mr; the same SQL on prod lists
    the four pairs (read-only, before the change).
  - assert_own_player_ids, assert_player_id_overrides_merged, assert_player_bio_conflicts_settled
    and the rest of the singular suite pass in data:build:mr.
  - A read-only ci_mr vs prod comparison shows the eight ids' matches, events and seasons moving
    as the blast radius says, and no other player's rows changing.
  - python scripts/ci_local.py --mr is green.

amendments: (none)
