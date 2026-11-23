# Task contract - a score that stopped at 90 minutes in a match decided after extra time is withheld, not a nightly stop

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." The test
  assert_extra_time_goals_counted_in_score fails the build on a match decided after extra time
  (AET, PEN) whose score equals its goal events of the first 90 minutes while an open-play goal or
  an own goal after minute 90 exists: the provider's score stopped at 90 minutes. Now a new base
  model, base_apif__fixtures_checked, holds that check. It reads base_apif__fixtures_next and the
  goal events of base_apif__fixture_events, so it sits downstream of the events and the events keep
  reading the unchecked fixtures. It sets the existing flag result_needs_research on such a match,
  blanks its score, shoot-out and winner as that flag already does, and carries the reason in
  score_stops_at_90. fct_fixture and the three base models that derive player and team values from
  the score (base_apif__fixture_players, base_apif__fixture_players_from_lineups,
  base_apif__fixture_statistics) read the checked model, so a wrong score reaches no value. The
  match is a result_withheld row of mart_competition_research_list until a row in
  fixture_result_corrections settles it. The test stays at error severity and proves the
  withholding against a stopped score it derives inline from the provider's score and the goal
  events, never from the flag.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). The extra-time score check named in the
  earlier handoff as the one check that needs a base-level score model, because the events read
  base_apif__fixtures_next and a flag on the score there would be a cycle. #327 describes the match
  status columns decided once in base; this change adds no status column.

depends_on:
  - none: every file this change edits is on gitlab/main, which holds the misfiled-team check; the branch is cut from it

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/macros/score_stopped_at_90.sql
  - dbt_project/models/2_base/api_football/base_apif__fixtures_checked.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_players_from_lineups_goals_add_up.sql
  - dbt_project/tests/assert_extra_time_goals_counted_in_score.sql
  - dbt_project/tests/assert_score_stopped_at_90_answer_key.sql
  - tests/test_extra_time_score_wiring.py
  - .claude/task/262-extra-time-score-withheld/contract.md
  - .claude/task/262-extra-time-score-withheld/review.md
  - .claude/task/262-extra-time-score-withheld/review_input.patch

impact_map: >
  writers: base_apif__fixtures_checked is a new base model written by dbt only (no ingestion code,
  no raw table); it reads base_apif__fixtures_next and base_apif__fixture_events. base_apif__fixtures_next
  reads stg_apif__fixtures_next and the seeds fixture_team_id_overrides, fixture_result_corrections
  and fixture_round_corrections; base_apif__fixture_events reads staging, base_apif__fixtures_next,
  base_apif__player_team_season and seeds, and no model that reads the checked model, so there is
  no cycle (`dbt parse` passes). The four readers that switch from base_apif__fixtures_next to the
  checked model are fct_fixture, base_apif__fixture_players, base_apif__fixture_players_from_lineups
  and base_apif__fixture_statistics; they are the only models that read the score columns
  (goals_home, goals_away, shootout_home, shootout_away, winner_team_id) and sit downstream of the
  events. base_apif__fixture_events keeps reading the unchecked score for its goal corrections.
  Direct readers (`dbt ls --select "<model>+1" --exclude <model> --resource-type model`):
  fct_fixture: fct_fixture_team_stats, int_competition_season__national_editions, int_knockout_ties,
  int_legs__player_match, int_legs__team_match, int_player__national_team_minutes,
  int_player__page_profile, int_player_page__window_seasons, int_team__current_national_competitions,
  int_team_momentum_window, mart_competition_fixtures, mart_competition_index,
  mart_competition_research_list, mart_fixture_standing_context, mart_leaderboards,
  mart_matchday_insights, mart_next_matchday, mart_player_fixture_stats, mart_player_momentum,
  mart_player_profile, mart_player_season_record, mart_team_fixtures, mart_team_index,
  mart_team_momentum_window, mart_team_season_record, mart_team_window_metrics.
  base_apif__fixture_players: base_apif__fixture_players_checked, base_apif__fixture_players_from_lineups,
  base_apif__lineup_sheets, base_apif__lineups, int_competition_season__player_stat_corrections,
  int_pipeline__corrections_no_longer_needed, mart_competition_research_list.
  base_apif__fixture_players_from_lineups: fct_fixture_player_stats, mart_competition_research_list.
  base_apif__fixture_statistics: base_apif__fixture_players, fct_fixture_team_stats.
  downstream (`dbt ls --select "<model>+" --resource-type model`, from the repo root with
  `--project-dir dbt_project`, on this branch cut from gitlab/main): fct_fixture 74 models, 685
  tests; base_apif__fixture_players 67, 538; base_apif__fixture_players_from_lineups 55, 486;
  base_apif__fixture_statistics 86, 684. As printed:
  fct_fixture (74): fct_fixture fct_fixture_team_stats int_competition_season__national_editions
  int_knockout_ties int_legs__player_match int_legs__team_from_players int_legs__team_match
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
  mart_player_season_record mart_player_squad_benchmarks mart_player_window_metrics mart_standings
  mart_team_competition_benchmarks mart_team_competitions mart_team_fixtures mart_team_index
  mart_team_leaderboards mart_team_momentum_window mart_team_page_window_metrics mart_team_profile
  mart_team_season mart_team_season_insights mart_team_season_record mart_team_window_metrics.
  base_apif__fixture_statistics (86): base_apif__fixture_events_checked base_apif__fixture_players
  base_apif__fixture_players_checked base_apif__fixture_players_from_lineups base_apif__fixture_statistics
  base_apif__lineup_sheets base_apif__lineups base_apif__players dim_player fct_fixture_event
  fct_fixture_lineup fct_fixture_player_stats fct_fixture_team_stats int_competition_season__player_stat_corrections
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
  mart_team_window_metrics.
  base_apif__fixture_players (67) is that list without 19 models: base_apif__fixture_statistics,
  fct_fixture_team_stats, int_legs__team_match, int_standings__official_rank, int_team_momentum_window,
  int_team_profile__streaks, int_team_season__biggest_results, int_team_season__longest_runs,
  int_team_season__standings_primary, int_team_season__table_by_time, int_team_season__table_legs,
  int_team_season__table_state, mart_competition_index, mart_competition_season_summary,
  mart_fixture_standing_context, mart_head_to_head, mart_next_matchday, mart_standings and
  mart_team_fixtures. base_apif__fixture_players_from_lineups (55) is the 67 without 12 models:
  base_apif__fixture_events_checked, base_apif__fixture_players, base_apif__fixture_players_checked,
  base_apif__lineup_sheets, base_apif__lineups, base_apif__players, dim_player, fct_fixture_event,
  fct_fixture_lineup, int_competition_season__player_stat_corrections,
  int_pipeline__corrections_no_longer_needed and mart_roster. The fct_fixture list (74) is the
  statistics list without 15 models (base_apif__fixture_events_checked, base_apif__fixture_players,
  base_apif__fixture_players_checked, base_apif__fixture_players_from_lineups,
  base_apif__fixture_statistics, base_apif__lineup_sheets, base_apif__lineups, base_apif__players,
  dim_player, fct_fixture_event, fct_fixture_lineup, fct_fixture_player_stats,
  int_competition_season__player_stat_corrections, int_pipeline__corrections_no_longer_needed and
  mart_roster) and with three models added (fct_fixture, int_competition_season__national_editions,
  int_knockout_ties). The new model's downstream is the union of the four lists: 89 models, plus
  itself.
  The change adds no column to a published model but result_needs_research, which already exists:
  fct_fixture keeps every column and takes goals_home, goals_away, shootout_home, shootout_away,
  winner_team_id and result_needs_research from the checked model.
  layer_rules: the check and the blanking are cleaning and sit in base; core reads base; the list
  reads the flag through fct_fixture as it does now; check_layer_contract applies unchanged: no
  per-competition file, no materialisation config in the model, no partition_by or cluster_by.
  deploy_order: one build; the nightly picks it up after merge. The checked model is a one-row-per-
  fixture table of the width of base_apif__fixtures_next, so the nightly stores one more copy of
  that table.
  blast_radius: measured read-only on prod before the build (45 MB scanned): 1,039 matches decided
  after extra time have goal events with a scorer; 0 of them have a score that stopped at 90
  minutes, so no published value changes today. The MR states the same measure on its ci_mr tables.

approved_design:
  - none: no page layout changes; a withheld result is served as not played with result_needs_research true, as the existing withheld results are

decisions_taken: >
  The smallest unit that is wrong is withheld: the match's score, shoot-out and winner, through the
  existing result_needs_research flag (#262, approved in chat, 15 Nov 2026). The test that caught
  the class stays at error severity and proves the withholding. The check reads the unchecked goal
  events of base_apif__fixture_events with a scorer, and a flagged score is derived in the test in
  SQL of its own from base_apif__fixtures_next and the same events, never from the flag. The base
  models that derive player and team values from the score read the checked model, so a goal count
  limited to a team's goals cannot use the understated figure. base_apif__fixture_events keeps the
  unchecked score, because it decides the goal corrections the check reads. Three error-severity
  tests recompute the cleaning rules of those readers from the score
  (assert_base_team_stats_cleaned, assert_base_player_stats_cleaned,
  assert_players_from_lineups_goals_add_up); each now reads the same checked score as the model it
  tests, so a withheld score cannot make a test and its model disagree. No condition, severity or
  filter of those tests changes. layering.md names the checked model as the source of fct_fixture.
  The new model is named
  after base_apif__fixture_events_checked and base_apif__fixture_players_checked and carries no
  status columns, which #327 places in base separately.

decisions_reserved: >
  none: how a withheld result looks on a page is the existing withheld-result form; no page,
  metric, name or rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes and sqlfluff lint passes on every changed model and macro
  - python -m pytest tests/test_extra_time_score_wiring.py passes, and fails with a reader switched back to base_apif__fixtures_next or the flag removed from the checked model
  - the MR pipeline is green, data:build:mr included

amendments: (none)
