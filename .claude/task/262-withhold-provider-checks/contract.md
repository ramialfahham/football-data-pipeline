# Task contract — five provider-data checks withhold the failing value instead of stopping the build

objective: >
  Issue #262: five error tests that catch the provider's data stopped the nightly from 11 to 14 Nov,
  and dbt skipped every model below them. Under the rule adopted for #262, a value that fails a
  check of the provider's data is withheld, the way cards_need_research withholds cards, and the
  check becomes an error test that every flagged value is blank and every other one passes. The
  five: (1) a competition-season whose share of corrected player rows passes 8%
  (stats_need_research) has its player and team boards withheld; (2) a standings section that
  resolves to a league table beside group or conference tables (kind_needs_research) is left out
  of mart_standings; (3) a team whose line-up players' goals do not add up to its score
  (goals_need_research) keeps its goals blank; (4) and (5) a team with no country, or whose country
  changed between deliveries with no team_country_corrections row (country_needs_research), has a
  blank country, and the one-national-team-per-country test stays on our code.

refs: >
  #262 and its What exactly / How as edited for this rule (approved in chat, 15 Nov 2026); routes
  ruled by the coordinating session on 2026-11-15: boards withheld for (1) (how a withheld board
  looks is #294); withhold, not hold, for (5); the new staging read over all team deliveries with
  only the columns it needs. Results are !446.

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__team_deliveries.sql
  - dbt_project/models/1_staging/api_football/README.md
  - dbt_project/tests/assert_player_match_cleaning_answer_key.sql
  - dbt_project/tests/assert_one_current_season_per_league.sql
  - dbt_project/tests/assert_team_benchmark_international_pool_is_the_league_phase.sql
  - dbt_project/tests/assert_mart_leaderboards_every_home_board_has_a_leader.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_fetches.sql
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_team.sql
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_state.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__standings_primary.sql
  - dbt_project/models/4_intermediate/shared/int_player_squad_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/models/4_intermediate/shared/int_competition_season__player_stat_corrections.sql
  - dbt_project/models/4_intermediate/shared/int_competition_season__player_stat_corrections.yml
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.sql
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.yml
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_team_index.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_player_squad_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_player_stat_corrections_within_limit.sql
  - dbt_project/tests/assert_every_standings_section_has_a_table_kind.sql
  - dbt_project/tests/assert_players_from_lineups_goals_add_up.sql
  - dbt_project/tests/assert_identity_fields_never_blanked.sql
  - .claude/task/262-withhold-provider-checks/contract.md
  - .claude/task/262-withhold-provider-checks/review.md
  - .claude/task/262-withhold-provider-checks/review_input.patch

impact_map: >
  writers: every changed model is written by dbt only; the new staging model reads
  raw.RAW_APIF_TEAMS (append-only, 0.24 GB, 3,006 rows on 2026-11-15), no ingestion code changes.
  downstream, `dbt ls --select <model>+ --resource-type model` and `--select <model>+,test_type:singular`
  on 2026-11-15 (stg_apif__team_deliveries+ is base_apif__teams_global+ plus itself):
  base_apif__fixture_fetches+ models: base_apif__fixture_fetches
  int_competition_season__player_stat_corrections int_player_squad_window__metrics mart_leaderboards
  mart_player_competition_benchmarks mart_player_squad_benchmarks mart_team_competition_benchmarks;
  singular tests: assert_mart_leaderboards_board_leader_order_is_total
  assert_mart_leaderboards_boards_follow_their_floors assert_mart_leaderboards_every_home_board_has_a_leader
  assert_mart_leaderboards_match_boards_follow_the_rule assert_mart_leaderboards_one_leader_per_league
  assert_mart_leaderboards_rank_ties_on_the_shown_value assert_one_current_season_per_league
  assert_player_metrics_follow_catalogue_formula assert_player_page_windows
  assert_player_peer_pools_follow_the_season_role assert_player_stat_corrections_within_limit
  assert_team_benchmark_international_pool_is_the_league_phase assert_team_benchmark_prev_season_matches_yoy
  assert_team_benchmark_rank_follows_direction.
  base_apif__teams_global+ models: base_apif__teams_global dim_player_team_season_mapping dim_team
  mart_competition_fixtures mart_fixture_standing_context mart_leaderboards mart_match_days
  mart_matchday_insights mart_player_career mart_player_fixture_stats mart_player_index
  mart_player_profile mart_roster mart_standings mart_team_competition_benchmarks mart_team_competitions
  mart_team_fixtures mart_team_index mart_team_leaderboards mart_team_market_value
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights; singular
  tests reading a country: assert_club_country_matches_domestic_league
  assert_continental_club_in_competition_confederation assert_identity_fields_never_blanked
  assert_player_nationality_matches_national_team assert_shown_teams_have_a_country
  assert_team_keeps_its_filled_row assert_team_name_slug_alphabet, and 55 more that read no country.
  int_standings__section_kinds+ models: int_standings__official_rank int_standings__section_kinds
  int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__standings_primary
  int_team_season__table_by_time int_team_season__table_state mart_competition_fixtures
  mart_competition_index mart_fixture_standing_context mart_match_days mart_matchday_insights
  mart_next_matchday mart_player_index mart_standings mart_team_competitions mart_team_index
  mart_team_profile mart_team_season mart_team_season_insights; singular tests reading the kind or
  standings: assert_every_standings_section_has_a_table_kind assert_standings_cross_group_rankings
  assert_standings_rank_follows_league_rule assert_team_standing_section_cases
  assert_team_table_equals_published_tables, and 29 more.
  base_apif__fixture_players_from_lineups+: 56 models, the whole player and team stat graph from
  fct_fixture_player_stats; singular tests that read the model by position or its goals:
  assert_player_match_cleaning_answer_key assert_players_from_lineups_goals_add_up, and 88 more
  that read fct_fixture_player_stats or later.
  layer_rules: flags are cleaning and sit in base, except (1) and (2): the share needs a
  competition-season grain and the section kind is first computed in intermediate, so their flags
  sit in intermediate; staging stays a plain unnest; check_layer_contract applies unchanged.
  deploy_order: one build; the nightly picks it up after merge. blast_radius: measured read-only on
  2026-11-15 from raw, (5) blanks the country of 5 teams (Al Khaleej Saihat 2928, KMKM 6423, KVZ
  8103, Mlandege 15567, Fassell 25192); (1), (2), (3) and (4) are measured on the MR's tables and
  stated in the MR.

approved_design:
  - none: no page layout changes; a withheld board, section, goals value or country is absent or blank, and how a withheld board looks is #294

decisions_taken: >
  Ruled by the coordinating session on 2026-11-15. (1) stats_need_research is the test's measure,
  moved into int_competition_season__player_stat_corrections: corrected share over 8% on matches
  whose latest fetch came 72 hours or more after kickoff, the latest fetch from the new
  base_apif__fixture_fetches over the four staging models of the fixture-details bundle. The boards
  leave the flagged competition-season out: mart_leaderboards, mart_player_competition_benchmarks
  and mart_team_competition_benchmarks by season_sk, mart_player_squad_benchmarks every squad whose
  window holds it. The test fails when a flagged competition-season is on a board, and keeps its
  named case. (2) kind_needs_research: a section whose kind resolves to league while its
  league-season has a group or conference section; a name matching two kinds and a served kind that
  differs from the rule stay errors on our code. (3) goals_need_research: the team scored and its
  goal events do not add up; its players' goals are already blank there. (4) and (5)
  country_needs_research: the team's final country is blank, because no delivery gave one or
  because its country changed between deliveries, compared after country_name_overrides, with no
  team_country_corrections row. Tests that require a country skip flagged teams; the unique test is
  unchanged. Each test stays error severity. (6) A withheld standings section is left out of the
  two team-season models that read the kinds too, so no team page takes a standing from it.
  (7) int_player_squad_window__metrics marks a squad whose window holds a flagged competition-season
  (stats_need_research), and mart_player_squad_benchmarks leaves it out. (8) fct_fixture_player_stats
  unions the two player models by position, so it drops goals_need_research from the line-up branch,
  and so does assert_player_match_cleaning_answer_key. (9) The boards compute every window before
  the withheld competition-season leaves: is_current_season stays on the latest season, so a
  league whose latest season is withheld has no current season, and
  assert_one_current_season_per_league excuses only that league, as
  assert_mart_leaderboards_every_home_board_has_a_leader and
  assert_team_benchmark_international_pool_is_the_league_phase excuse a withheld competition-season.
  (10) What is withheld is the
  ranking of a flagged competition-season. A team's own previous-season value
  (metric_value_prev_season) stays, as the team page's year-on-year shows it. A player's
  competition_order counts the competitions served.
  (11) A flagged competition-season always has a season_sk (not_null test), so the withholding
  cannot miss it.

decisions_reserved:
  - How a withheld board, section or country shows on the site: #294 and site tasks.
  - The daily list that reads the flags: #262's How, its own task.
  - assert_team_stat_corrections_within_limit and assert_extra_time_goals_counted_in_score.

done_when:
  - dbt parse passes; sqlfluff lint passes on the changed models and tests; the full pytest suite passes.
  - The MR's data build runs every model and every test passes.
  - The MR states, measured read-only on its tables, the competition-seasons flagged stats_need_research and the boards that hides, the flagged standings sections, line-up teams and countries, and the new staging model's nightly bytes.
