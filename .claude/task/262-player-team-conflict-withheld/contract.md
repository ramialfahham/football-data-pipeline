# Task contract - a player whose stat line and match events name different teams is withheld and listed, not a nightly stop

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." The test
  assert_player_row_and_events_same_team fails the build on a player whose stat line and match
  events, own goals aside, name different teams. Two things leave a conflict standing after the
  player's-team rule of the cleaning rules: an event filed under a team that did not play the match
  (withheld since the misfiled-team check) and a dispute between the two teams of the match that
  the squad list and the player's other matches cannot decide. The second is the provider
  contradicting itself. Now such a player carries player_team_needs_research in the event model,
  the player-line models and the line-up model: his events and his stat line of that match leave
  fct_fixture_event and fct_fixture_player_stats, and the match is a player_team_withheld row of
  mart_competition_research_list until a row in fixture_lineup_corrections names his team. The test
  stays at error severity and proves the withholding of both kinds against conflicts it derives
  inline from the match's two teams in fct_fixture.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). The coordinating session classified the
  test as a provider-data check that still stopped the nightly and ruled the plan: case (i), an
  event under a team of another match, is derived inline and left to the misfiled-team flag; case
  (ii), an undecided dispute between the two teams of the match, is withheld until a
  fixture_lineup_corrections row decides.

depends_on:
  - none: every file this change edits is on gitlab/main, which holds the misfiled-team check. The open merge request for the extra-time score check edits base_apif__fixture_players_from_lineups.sql and fct_fixture.sql in other places; a merge of main resolves it

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/macros/player_team_disputes.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events_checked.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_checked.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/5_marts/shared/mart_competition_research_list.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_player_row_and_events_same_team.sql
  - dbt_project/tests/assert_player_team_disputes_answer_key.sql
  - dbt_project/tests/assert_player_match_cleaning_answer_key.sql
  - dbt_project/tests/assert_stat_facts_equal_base.sql
  - dbt_project/tests/assert_team_stat_blank_counts_follow_the_blank_rule.sql
  - tests/test_player_team_conflict_wiring.py
  - tests/test_misfiled_team_wiring.py
  - .claude/skills/research-provider-errors/SKILL.md
  - .claude/task/262-player-team-conflict-withheld/contract.md
  - .claude/task/262-player-team-conflict-withheld/review.md
  - .claude/task/262-player-team-conflict-withheld/review_input.patch

impact_map: >
  writers: the three base models, the two facts and the mart are written by dbt only (no
  ingestion code, no raw table). base_apif__fixture_events_checked reads base_apif__fixture_events,
  base_apif__lineups, base_apif__fixtures_next and, new, base_apif__fixture_players;
  base_apif__fixture_players_checked reads base_apif__fixture_players, base_apif__fixture_events and
  base_apif__fixture_events_checked; base_apif__fixture_players_from_lineups reads the line-up
  sheets, base_apif__fixture_events_checked and, new, base_apif__fixture_players and
  base_apif__fixture_events. There is no cycle: base_apif__fixture_players reads
  base_apif__fixture_player_lines and base_apif__fixture_events, never a checked model, and
  base_apif__lineups reads base_apif__fixture_players (`dbt ls` and `dbt parse` pass). Direct
  readers (`dbt ls --select "<model>+1" --exclude <model> --resource-type model`):
  base_apif__fixture_events_checked: base_apif__fixture_players_checked,
  base_apif__fixture_players_from_lineups, fct_fixture_event, int_pipeline__corrections_no_longer_needed,
  mart_competition_research_list. base_apif__fixture_players_checked: fct_fixture_player_stats,
  mart_competition_research_list. base_apif__fixture_players_from_lineups: fct_fixture_player_stats,
  mart_competition_research_list. fct_fixture_event: mart_competition_fixtures,
  mart_competition_research_list. fct_fixture_player_stats: int_legs__player_match,
  int_player__page_profile, mart_competition_fixtures, mart_leaderboards, mart_player_fixture_stats,
  mart_player_profile. mart_competition_research_list: none.
  The new column player_team_needs_research is added after team_needs_research in the three base
  models, so fct_fixture_player_stats, which unions base_apif__fixture_players_checked and
  base_apif__fixture_players_from_lineups by position, keeps its columns; the facts do not output
  it. assert_player_match_cleaning_answer_key unions the line-up model by position and excepts the
  new column. The research list gains a check_name and a seed value and no column.
  downstream (`dbt ls --select "<model>+" --resource-type model`, from the repo root with
  `--project-dir dbt_project`, on this branch cut from gitlab/main), counts and tests:
  base_apif__fixture_events_checked 59 models, 511 tests; base_apif__fixture_players_checked 55,
  482; base_apif__fixture_players_from_lineups 55, 488; fct_fixture_event 7, 96;
  fct_fixture_player_stats 54, 478; mart_competition_research_list 1, 14. As printed:
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
  base_apif__fixture_players_checked (55) and base_apif__fixture_players_from_lineups (55): each is
  itself plus the 54-model list of fct_fixture_player_stats, which is the 59 above without
  base_apif__fixture_events_checked, base_apif__fixture_players_checked,
  base_apif__fixture_players_from_lineups, fct_fixture_event and int_pipeline__corrections_no_longer_needed.
  fct_fixture_event (7): fct_fixture_event mart_competition_fixtures mart_competition_research_list
  mart_match_days mart_player_index mart_team_competitions mart_team_index.
  layer_rules: the flag is cleaning and sits in base; the facts leave the flagged lines out; the
  list is a mart that reads base, as it does now; check_layer_contract applies unchanged: no new
  model, no materialisation change, no per-competition file.
  deploy_order: one build; the nightly picks it up after merge. A flag with no failing input
  changes no value.
  blast_radius: measured read-only on prod before the build: the conflict the test returns
  (a player's stat line and events naming different teams) holds for 0 players, so no published
  value changes today. The MR states the same measure on its ci_mr tables.

approved_design:
  - none: no page output changes; a withheld line leaves the facts as a line the provider never sent

decisions_taken: >
  The smallest unit that is wrong is withheld: the player's stat line and events of the match,
  because the provider contradicts itself and nothing in our data says which side is right (#262,
  approved in chat, 15 Nov 2026). The test that caught the class stays at error severity and
  proves the withholding; no test gets a where exemption, a lower severity or a filter that hides
  rows. A dispute is a player whose stat line names one team of the match and whose events, own
  goals and hand-corrected goals and cards aside, name the other team of the match: the same
  condition as the test, and the one the player's-team rule leaves standing where it cannot decide.
  The test derives its conflicts inline from fct_fixture and the base lines, and requires: a
  dispute between the two teams of the match is flagged, an event or stat line under a team of
  another match is flagged by the misfiled-team flag, no line is flagged without a conflict, no
  fact holds a flagged line, and each flagged match is on the list. assert_stat_facts_equal_base
  compares each fact with its base; its base side of the player facts also leaves out the lines of
  a player in a dispute, derived in inline SQL as in the test above and never from the flag, at
  error severity, as it already leaves out the lines under a team of another match. The wiring test
  assert_team_stat_blank_counts_follow_the_blank_rule counts the players with an offside of a
  team from the fact; it adds the offsides of the players in a dispute, derived inline as above,
  because base keeps a team's blank offsides count where such a player had one. The wiring test
  of the misfiled-team flag changes where the new column and the new facts filter change the
  rendered text it pins; each pin still fails when its own wiring is removed. The match is a
  player_team_withheld row naming fixture_lineup_corrections, the seed whose researched sheet
  decides a player's team; the research skill does not research it, because it does no line-up
  research.

decisions_reserved: >
  none: how a withheld line looks on a page is the absence of the line; no page, metric, name or
  rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes and sqlfluff lint passes on every changed model and macro
  - python -m pytest tests/test_player_team_conflict_wiring.py passes, and fails with a facts filter, a flag column or the mart branch removed
  - the MR pipeline is green, data:build:mr included

amendments: (none)
