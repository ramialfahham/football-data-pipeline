# Task contract - a line-up the provider stored twice with different content is withheld and listed

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." The staging
  test stg_apif__lineups_order_keys_unique and the base test assert_lineup_fetches_never_tie stop the
  build when the provider's response lists one fixture's line-up twice at one ingest time (a "tie").
  The cause is provider data: the loader writes one raw row per element of the provider's batch response
  with one ingest time per call (ingestion/api_football/loads/batch_fixtures.py:96-107). Now a tie of
  identical sheets collapses to one sheet in base and nothing is lost; a tie whose sheets DIFFER withholds
  the sheet of that team (no sheet of the team reaches base_apif__lineup_sheets, base_apif__lineups,
  fct_fixture_lineup or the player lines read from line-ups; the other team keeps its sheet and the
  match line-up is not_available, as for any match with one sheet) and the match is listed on
  mart_competition_research_list as lineup_duplicate_withheld. A fetch newer than the tie removes the row.
  A grid lender among older fetches lends nothing when the fetches tied at its ingest time differ.
  The base uniqueness tests stay at error. assert_lineup_fetches_never_tie becomes the proof that no
  differing tie reaches a published value. A hand-written answer key runs identical and differing ties,
  and a column we add to a row, through the macro that finds them, and python pins fix the wiring. The
  staging test is removed.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). The coordinating session ruled: the staging
  uniqueness tests are provider-data checks and go; in base, tied rows that are identical collapse to one
  and tied rows that differ are withheld, never picked by a tie-break; the match is listed on
  mart_competition_research_list whenever it can be identified; the base unique tests stay at error.
  This change covers the line-ups (stg_apif__lineups). The other five staging uniqueness tests
  (fixtures_next, fixture_events, teams, leagues, standings) are their own changes.

depends_on:
  - none: every file this change edits is on gitlab/main

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/macros/newest_fetch_ties.sql
  - dbt_project/models/2_base/api_football/base_apif__lineup_fetches.sql
  - dbt_project/models/2_base/api_football/base_apif__lineup_fetch_ties.sql
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/2_base/api_football/base_apif__lineup_sheets.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/5_marts/shared/mart_competition_research_list.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_lineup_fetches_never_tie.sql
  - dbt_project/tests/assert_newest_fetch_ties_answer_key.sql
  - dbt_project/tests/assert_lineup_fetch_keeps_grid_only_for_same_eleven.sql
  - tests/test_lineup_ties_wiring.py
  - tests/test_player_team_conflict_wiring.py
  - .claude/skills/research-provider-errors/SKILL.md
  - .claude/task/262-lineup-ties-withheld/contract.md
  - .claude/task/262-lineup-ties-withheld/review.md
  - .claude/task/262-lineup-ties-withheld/review_input.patch

impact_map: >
  writers: one staging test removed, two base models (base_apif__lineup_fetches, which takes the
  team-id correction out of base_apif__lineup_sheets, and base_apif__lineup_fetch_ties) and one macro
  added, two base models change (base_apif__lineup_sheets, base_apif__fixture_players), one sentence
  added to the Line-ups rule of the cleaning_rules doc block, one mart branch and one row kind added, one
  base test rewritten, one answer key added, one existing pin test
  (tests/test_player_team_conflict_wiring.py) no longer asserts that the branch of player_team_withheld
  closes the items CTE, and assert_lineup_fetch_keeps_grid_only_for_same_eleven picks its grid lender
  the way base does. assert_lineup_fetches_never_tie reads the sheets from base_apif__lineup_fetches
  (the team after the correction) and compares them as JSON itself, never through the macro or the
  ties model. The tests that read the line-up from staging and start from base rows
  (assert_lineup_two_people_one_id_not_held, assert_sheet_and_stats_player_join_on_shirt) cannot fail on
  a team left out of base; assert_names_carry_no_html_entity and base_apif__fixture_fetches read names
  and ingest times only. The test removed (`dbt ls --select stg_apif__lineups --resource-type test`):
  stg_apif__lineups_order_keys_unique. The base proof stays: base_apif__lineup_sheets carries
  unique_combination_of_columns on (league_code, fixture_id, team_id, is_starter, sheet_index).
  The changed models and their readers, pasted from `dbt ls --select <model>+ --resource-type model`
  (the .venv dbt, repo root):
  base_apif__lineup_sheets+ and base_apif__fixture_players+ (union): base_apif__fixture_events_checked,
  base_apif__fixture_players, base_apif__fixture_players_checked, base_apif__fixture_players_from_lineups,
  base_apif__lineup_sheets, base_apif__lineups, base_apif__players, dim_player, fct_fixture_event,
  fct_fixture_lineup, fct_fixture_player_stats, int_competition_season__player_stat_corrections,
  int_legs__player_match, int_legs__team_from_players, int_pipeline__corrections_no_longer_needed,
  int_player__national_team_minutes, int_player__page_profile, int_player_club_season__metrics,
  int_player_competition_benchmark_metrics_long, int_player_competition_benchmarks,
  int_player_match__metrics, int_player_momentum__metrics, int_player_page__window_seasons,
  int_player_profile__contribution, int_player_season__metrics, int_player_season__team,
  int_player_season_position__metrics, int_player_season_record, int_player_squad_window__metrics,
  int_player_window__metrics, int_team__current_national_competitions, int_team__featured_season,
  int_team_competition_benchmark_metrics_long, int_team_competition_benchmarks,
  int_team_competition_phase__metrics, int_team_momentum__metrics, int_team_season__deserved_vs_actual,
  int_team_season__metrics, int_team_season__metrics_cumulative, int_team_season_record,
  int_team_window__metrics, mart_competition_fixtures, mart_competition_research_list, mart_leaderboards,
  mart_match_days, mart_matchday_insights, mart_player_career, mart_player_competition_benchmarks,
  mart_player_fixture_stats, mart_player_index, mart_player_momentum, mart_player_profile,
  mart_player_season_record, mart_player_squad_benchmarks, mart_player_window_metrics, mart_roster,
  mart_team_competition_benchmarks, mart_team_competitions, mart_team_index, mart_team_leaderboards,
  mart_team_momentum_window, mart_team_page_window_metrics, mart_team_profile, mart_team_season,
  mart_team_season_insights, mart_team_season_record, mart_team_window_metrics.
  mart_competition_research_list+ : mart_competition_research_list. The new base model
  base_apif__lineup_fetch_ties is read by base_apif__lineup_sheets, base_apif__fixture_players and the
  mart.
  downstream: prod holds no tie today (the staging test and assert_lineup_fetches_never_tie pass), so no
  row, no number and no page changes.
  layer_rules: base models, one macro, one mart branch, tests; check_layer_contract applies unchanged.
  deploy_order: one build; the nightly picks it up after merge.
  blast_radius: none for any model or value today. A provider tie no longer stops the nightly: an
  identical tie collapses, a differing tie withholds the match's line-up and lists the match.

approved_design:
  - none: no page output changes

decisions_taken: >
  Ruled by the coordinating session on #262's approved rule (approved in chat, 15 Nov 2026). A tie is
  the rows of one team's sheet in one match that carry the same ingest time as the newest fetch; its
  rows are identical when farm_fingerprint(to_json_string(row)) is equal for all of them; the
  fingerprint covers the provider's content only (raw_ingested_at is ours and is left out; the
  macro takes the columns to leave out). Only the team whose tied sheets differ is withheld: its
  match then has one sheet, which base_apif__lineups already marks not_available (check two_sheets),
  so no reader needs both sides together. A newer fetch without the tie removes the withhold and the
  row; a tie among older fetches never withholds the team, but the grid lender lends nothing when the
  fetches tied at its ingest time differ. A team is the team after fixture_team_id_overrides, so two
  provider ids of one team in one fixture at one ingest time are tied: identical sheets collapse,
  differing sheets are withheld and listed. base_apif__lineup_fetches holds the sheets under that
  team id, and the ties model, base_apif__lineup_sheets and the line-up read of
  base_apif__fixture_players read it. No seed fixes the row, so its seed value is none (engineering decision, working
  agreement section 10 unclear cases, as is the row kind name lineup_duplicate_withheld, one kind per
  table so that the later places of this rule cannot share an item_key).

decisions_reserved: >
  none: no page, metric, name or rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes
  - python -m pytest tests/test_lineup_ties_wiring.py passes, and fails with the macro, the ties model, a base filter, the mart branch or a test changed
  - the MR pipeline is green, data:build:mr included

amendments: (none)
