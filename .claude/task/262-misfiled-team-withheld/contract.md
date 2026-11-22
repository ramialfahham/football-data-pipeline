# Task contract - a line the provider filed under a team that did not play the match is withheld and listed, not a nightly stop

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." Four
  tests stop the build when an event, a player stat line or a match statistics line is filed under
  a team that is not one of the match's two teams:
  assert_event_team_in_fixture_participants, assert_player_stats_team_in_fixture_participants,
  assert_team_stats_team_in_fixture_participants and, through the line-up path,
  assert_stat_facts_equal_base. Now the line carries team_needs_research in base
  (base_apif__fixture_events_checked, base_apif__fixture_players_checked,
  base_apif__fixture_players_from_lineups, base_apif__fixture_statistics), the two facts that take
  a line (fct_fixture_event, fct_fixture_player_stats) leave it out, and the match is a
  misfiled_team_withheld row of mart_competition_research_list until a row in
  fixture_team_id_overrides files the line under the right team. The row carries the provider's
  team id in its own column, provider_team_id, and a team_sk only where the team is in dim_team,
  so the research list keeps its relationships test on every row kind. The test that caught the
  class stays at error severity and proves the withholding.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). The last of the three provider checks
  that move from stopping the nightly to withholding; the player bio conflict and the two-team
  card check are the first two. The extra-time score check, the standings checks and the null-key
  checks are not part of this change.

depends_on:
  - none: every file this change edits is on gitlab/main; the new Python test carries its own render helper

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/macros/team_not_in_fixture.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events_checked.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_checked.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/5_marts/shared/mart_competition_research_list.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_team_stats_team_in_fixture_participants.sql
  - dbt_project/tests/assert_stat_facts_equal_base.sql
  - dbt_project/tests/assert_player_match_cleaning_answer_key.sql
  - dbt_project/tests/assert_misfiled_team_lines_withheld.sql
  - dbt_project/tests/assert_misfiled_team_answer_key.sql
  - tests/test_misfiled_team_wiring.py
  - tests/test_no_decision_history_in_code.py
  - .claude/skills/research-provider-errors/SKILL.md
  - .claude/task/262-misfiled-team-withheld/contract.md
  - .claude/task/262-misfiled-team-withheld/review.md
  - .claude/task/262-misfiled-team-withheld/review_input.patch

impact_map: >
  writers: the four base models, the two facts and the mart are written by dbt only (no
  ingestion code, no raw table); base_apif__fixture_events_checked reads base_apif__fixture_events,
  base_apif__fixture_players_checked reads base_apif__fixture_players,
  base_apif__fixture_players_from_lineups reads the line-up sheets and the events,
  base_apif__fixture_statistics reads stg_apif__fixture_statistics, and all four read
  base_apif__fixtures_next for the match's two teams. Direct readers
  (`dbt ls --select "<model>+1" --exclude <model> --resource-type model`):
  base_apif__fixture_events_checked: base_apif__fixture_players_checked,
  base_apif__fixture_players_from_lineups, fct_fixture_event, int_pipeline__corrections_no_longer_needed.
  base_apif__fixture_players_checked: fct_fixture_player_stats.
  base_apif__fixture_players_from_lineups: fct_fixture_player_stats, mart_competition_research_list.
  base_apif__fixture_statistics: base_apif__fixture_players, fct_fixture_team_stats.
  fct_fixture_event: mart_competition_fixtures, mart_competition_research_list.
  fct_fixture_player_stats: int_legs__player_match, int_player__page_profile, mart_competition_fixtures,
  mart_leaderboards, mart_player_fixture_stats, mart_player_profile.
  mart_competition_research_list: none. The new column team_needs_research is added at the end of
  the player-line models, so fct_fixture_player_stats, which unions base_apif__fixture_players_checked
  and base_apif__fixture_players_from_lineups by position, keeps its columns; the facts do not output
  it. The research list gains one column, provider_team_id; no model reads the list.
  downstream (`dbt ls --select "<model>+" --resource-type model`, from the repo root with
  `--project-dir dbt_project`, on this branch cut from gitlab/main), counts and tests: 
  base_apif__fixture_events_checked 59 models, 491 tests; base_apif__fixture_players_checked 55, 476;
  base_apif__fixture_players_from_lineups 55, 478; base_apif__fixture_statistics 86, 663;
  fct_fixture_event 7, 94; fct_fixture_player_stats 54, 476; mart_competition_research_list 1, 12.
  The model lists, as printed:
  base_apif__fixture_events_checked (59): base_apif__fixture_events_checked base_apif__fixture_players_checked
  base_apif__fixture_players_from_lineups fct_fixture_event fct_fixture_player_stats int_legs__player_match
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
  mart_player_season_record mart_player_squad_benchmarks mart_player_window_metrics
  mart_team_competition_benchmarks mart_team_competitions mart_team_index mart_team_leaderboards
  mart_team_momentum_window mart_team_page_window_metrics mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record mart_team_window_metrics.
  base_apif__fixture_players_checked (55) and fct_fixture_player_stats (54): the same list from
  fct_fixture_player_stats on (the first also holds itself); base_apif__fixture_players_from_lineups
  (55): itself and that list.
  base_apif__fixture_statistics (86): the 59 above, minus nothing, plus base_apif__fixture_players,
  base_apif__fixture_statistics, base_apif__lineup_sheets, base_apif__lineups, base_apif__players,
  dim_player, fct_fixture_lineup, fct_fixture_team_stats, int_competition_season__player_stat_corrections,
  int_legs__team_match, int_standings__official_rank, int_team_momentum_window, int_team_profile__streaks,
  int_team_season__biggest_results, int_team_season__longest_runs, int_team_season__standings_primary,
  int_team_season__table_by_time, int_team_season__table_legs, int_team_season__table_state,
  mart_competition_index, mart_competition_season_summary, mart_fixture_standing_context,
  mart_head_to_head, mart_next_matchday, mart_roster, mart_standings, mart_team_fixtures.
  fct_fixture_event (7): fct_fixture_event mart_competition_fixtures mart_competition_research_list
  mart_match_days mart_player_index mart_team_competitions mart_team_index.
  layer_rules: the flags are cleaning and sit in base; the facts leave the flagged lines out; the
  list is a mart that reads base, as it does now; check_layer_contract applies unchanged: no new
  model, no materialisation change, no per-competition file.
  deploy_order: one build; the nightly picks it up after merge. A flag with no failing input
  changes no value.
  blast_radius: measured read-only on prod before the build (53 MB scanned): 0 events, 0 player
  lines, 0 line-up players and 0 statistics lines are filed under a team that is not one of the
  match's two teams, so no published value changes today. The MR states the same measure on its
  ci_mr tables.

approved_design:
  - none: no page output changes; a withheld line leaves the facts as a line the provider never sent

decisions_taken: >
  The smallest unit that is wrong is withheld: the line (#262, approved in chat, 15 Nov 2026).
  The test that caught the class stays at error severity and proves the withholding; no test moves
  to warn. The misfiled line stays in base, flagged, because other tests need every fetched line
  in base. The research list carries the provider's team id in provider_team_id and a team_sk only
  where the team is in dim_team, so the error-severity relationships test of team_sk to dim_team
  holds on every row kind. The misfiled-team row names fixture_team_id_overrides as its seed; the
  research skill does not research it, because the skill does not edit that seed.
  Engineering decision, ruled by the coordinating session: assert_stat_facts_equal_base compares
  each fact with its base, and base keeps a misfiled line that the fact leaves out, so its base
  side leaves out the lines that are misfiled; assert_team_stats_team_in_fixture_participants
  requires a misfiled statistics line to be flagged. Both stay at error severity. The lines that
  are misfiled are derived in inline SQL from the match's two teams in fct_fixture
  (home_team_api_id, away_team_api_id), never from the flag and not through the macro that sets
  it, so an over-flagged line of a team of the match still fails the equality test, and a fault in
  the macro cannot hide on both sides. assert_misfiled_team_lines_withheld holds the left-out lines
  to account in both directions, with the same inline derivation.
  A match with an event filed under a team that did not play it has no full events for the
  line-up path of base_apif__fixture_players_from_lineups, so none of its line-up players has
  proven cards: the card has no team to count for, and counting it as 0 would publish a wrong
  value. The research list's lineup_goals_withheld branch leaves out a flagged line-up line,
  which the misfiled-team row already lists, so no row of the list carries a provider team id in
  team_sk.

decisions_reserved: >
  none: how a withheld line looks on a page is the absence of the line; no page, metric, name or
  rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes and sqlfluff lint passes on every changed model and macro
  - python -m pytest tests/test_misfiled_team_wiring.py passes, and fails with a facts filter, a flag column or the mart provider_team_id wiring removed
  - the MR pipeline is green, data:build:mr included

amendments: (none)
