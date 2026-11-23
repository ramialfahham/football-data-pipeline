# Task contract - a team's card count is not shown as 0 in a match whose events name a team that did not play it

objective: >
  Issue #262, outside item found in the review of the misfiled-team check. base_apif__fixture_statistics
  fills a team's blank yellow or red card count with 0 where the match's events were delivered and
  the team has no event of that colour or of none. A card event filed under a team that did not
  play the match counts against no team of the match, so a team whose line carries no count and
  whose card sits under that third team gets a 0 that is a wrong value, not the provider's. Now a
  match with such an event proves no team's card count to be 0: the blank stays blank, as it does
  where nothing proves the count. The match is already a misfiled_team_withheld row of
  mart_competition_research_list through that event. The test that recomputes the fill rule,
  assert_base_team_stats_cleaned, stays at error severity, leaves a blank card count of such a
  match out of its blank-where-events-prove-none rule, and fails a 0 that such a match fills from
  its events.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). The coordinating session ruled the item
  after the analytics review of the misfiled-team check: a wrong value, withheld in base on the
  same pattern, tests at error, no flag filters.

depends_on:
  - none: every file this change edits is on gitlab/main, which holds the misfiled-team check

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_fixture_statistics_from_every_fetch.sql
  - tests/test_statistics_card_fill_wiring.py
  - .claude/task/262-statistics-yellow-unknown/contract.md
  - .claude/task/262-statistics-yellow-unknown/review.md
  - .claude/task/262-statistics-yellow-unknown/review_input.patch

impact_map: >
  writers: base_apif__fixture_statistics is written by dbt only (no ingestion code, no raw table);
  it reads stg_apif__fixture_statistics, base_apif__fixtures_next, base_apif__fixture_events,
  base_apif__fixture_player_lines and seeds. The change adds one internal column,
  has_misfiled_event, to its match_events and in_context steps and changes two fill expressions
  (cards_yellow_filled, cards_red_filled); the model's output columns are unchanged. It uses the
  macro team_not_in_fixture that the misfiled-team check added. Direct readers
  (`dbt ls --select "base_apif__fixture_statistics+1" --exclude base_apif__fixture_statistics
  --resource-type model`): base_apif__fixture_players, fct_fixture_team_stats,
  mart_competition_research_list.
  downstream (`dbt ls --select "base_apif__fixture_statistics+" --resource-type model`, from the repo
  root with `--project-dir dbt_project`, on this branch cut from gitlab/main): 86 models, 689 tests.
  As printed: base_apif__fixture_events_checked base_apif__fixture_players base_apif__fixture_players_checked
  base_apif__fixture_players_from_lineups base_apif__fixture_statistics base_apif__lineup_sheets
  base_apif__lineups base_apif__players dim_player fct_fixture_event fct_fixture_lineup
  fct_fixture_player_stats fct_fixture_team_stats int_competition_season__player_stat_corrections
  int_legs__player_match int_legs__team_from_players int_legs__team_match int_pipeline__corrections_no_longer_needed
  int_player__national_team_minutes int_player__page_profile int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_match__metrics int_player_momentum__metrics int_player_page__window_seasons
  int_player_profile__contribution int_player_season__metrics int_player_season__team
  int_player_season_position__metrics int_player_season_record int_player_squad_window__metrics
  int_player_window__metrics int_standings__official_rank int_team__current_national_competitions
  int_team__featured_season int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_competition_phase__metrics int_team_momentum__metrics int_team_momentum_window
  int_team_profile__streaks int_team_season__biggest_results int_team_season__deserved_vs_actual
  int_team_season__longest_runs int_team_season__metrics int_team_season__metrics_cumulative
  int_team_season__standings_primary int_team_season__table_by_time int_team_season__table_legs
  int_team_season__table_state int_team_season_record int_team_window__metrics mart_competition_fixtures
  mart_competition_index mart_competition_research_list mart_competition_season_summary
  mart_fixture_standing_context mart_head_to_head mart_leaderboards mart_match_days
  mart_matchday_insights mart_next_matchday mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_index mart_player_momentum mart_player_profile
  mart_player_season_record mart_player_squad_benchmarks mart_player_window_metrics mart_roster
  mart_standings mart_team_competition_benchmarks mart_team_competitions mart_team_fixtures
  mart_team_index mart_team_leaderboards mart_team_momentum_window mart_team_page_window_metrics
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record
  mart_team_window_metrics. The test that recomputes the rule is assert_base_team_stats_cleaned.
  layer_rules: the rule is cleaning and sits in base; check_layer_contract applies unchanged: no new
  model, no materialisation change, no per-competition file.
  deploy_order: one build; the nightly picks it up after merge. A rule with no failing input
  changes no value.
  blast_radius: measured read-only on prod before the build: 0 events are filed under a team that
  did not play the match, so no team line changes today. The MR states the same measure on its
  ci_mr tables.

approved_design:
  - none: no page output changes; a card count that is not proven is blank, as it is where nothing proves it today

decisions_taken: >
  The smallest unit that is wrong is withheld: the filled 0 stays blank (#262, approved in chat,
  15 Nov 2026). The cause is a card event under a team of another match, which the misfiled-team
  check already lists; no new list row is added. The model reads the unchecked events, as it must,
  because the checked events read the line-ups, which read this model. The match's misfiled events
  are derived in the model with the macro of the misfiled-team check. The test that recomputes the
  fill rule derives the same matches inline from the match's two teams in base_apif__fixtures_next,
  never through the macro, so a fault in the macro cannot hide on both sides; it stays at error
  severity, and its new rule fails a 0 that such a match fills from its events; the rule counts a
  count as delivered when any fetch carried it, as the model keeps the newest value of any fetch.
  The same matches also stop the card bounds of the events from blanking a card count an earlier
  fetch carried, because the events of such a match bound no team's count: the model's
  matches_with_events leaves them out, and assert_fixture_statistics_from_every_fetch, which
  recomputes that bound, leaves them out by the same inline derivation. A dispute between
  the two teams of a match, which can also leave a card under the other team, is left to a later
  change, because the model cannot read the line-up and player-line models that decide it.

decisions_reserved: >
  none: how a blank count looks on a page is the existing blank form; no page, metric, name or
  rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes and sqlfluff lint passes on every changed model
  - python -m pytest tests/test_statistics_card_fill_wiring.py passes, and fails with the has_misfiled_event guard removed from either fill
  - the MR pipeline is green, data:build:mr included

amendments: (none)
