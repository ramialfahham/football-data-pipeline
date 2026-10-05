# Task contract — match events come only from each match's latest fetch

objective: >
  A match's events are those of its latest fetch that has events. Base keeps only that fetch's
  rows; fct_fixture_event is rebuilt in full every night from base, so 32 stale events in 8
  matches (25 of them goals) leave the fact; a singular test fails on any event beyond the latest
  fetch.

refs: >
  #201. Plan approved by the CPO in chat, 2026-10-05.

acceptance_criteria:
  - Every match's events are the events of its latest fetch that has events; no event from an older, longer fetch remains (today: 32 stale events in 8 matches, 25 of them goals)
  - Numbers built on match events change only for those 8 matches
  - A test fails when a match holds an event its latest fetch does not have

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/tests/assert_fixture_events_only_from_latest_fetch.sql
  - dbt_project/tests/assert_no_event_loss_since_cutoff.sql
  - dbt_project/dbt_project.yml
  - dbt_project/docs/layering.md
  - tests/test_no_decision_history_in_code.py
  - docs/data_contract.md
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - ingestion/api_football/loads/batch_fixtures.py
  - tests/test_incomplete_fetch_no_supersede.py
  - dbt_project/tests/assert_fanout_facts_not_empty.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - docs/tracker/**

impact_map: >
  writers: stg_apif__fixture_events (all fetches, from RAW_APIF_FIXTURE_DETAILS, append-only) →
  base_apif__fixture_events (the only writer of base events) → fct_fixture_event (only reader of base
  events in core).
  downstream (`dbt ls --select base_apif__fixture_events+ --resource-type model`, pasted):
  base_apif__fixture_events base_apif__fixture_players base_apif__fixture_statistics
  base_apif__players dim_player fct_fixture_event fct_fixture_player_stats fct_fixture_team_stats
  int_legs__player_match int_legs__team_from_players int_legs__team_match
  int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_momentum__metrics int_player_profile__contribution
  int_player_profile__yoy int_player_season__metrics int_player_season__team
  int_player_season_position__metrics int_player_season_record
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season_record mart_competition_fixtures
  mart_competition_season_summary mart_head_to_head mart_leaderboards mart_match_days
  mart_matchday_insights mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_match_log mart_player_momentum mart_player_profile
  mart_player_season_record mart_roster mart_team_competition_benchmarks mart_team_fixture_stats
  mart_team_fixtures mart_team_leaderboards mart_team_momentum mart_team_momentum_window
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record
  layer_rules: base dedups (layering §2_base); a 3_core fact sets no materialisation of its own once
  it is not incremental (check_layer_contract.py); no partition_by or cluster_by.
  deploy_order: on merge the 04:00 nightly rebuilds base and builds fct_fixture_event as a table in
  place of the incremental one; nothing runs between merge and the nightly. The MR build writes
  only ci_mr datasets.
  blast_radius: measured on prod (two queries, 40.5 MB and 47.4 MB): 56,286 matches, 116 fetched
  more than once; base holds 15 stale events in 6 matches, the fact 32 in 8 (17 no longer in base);
  fact events of matches missing from raw: 0. Numbers built on events change for those 8 matches
  only: phantom goals in 4 (they contradict the official score), last-minute cards in 3, and the
  kicks of 2 shoot-outs that every reader excludes.

decisions_taken: >
  The plan in #201, approved by the CPO in chat, 2026-10-05. Readings, under the delegation of
  2026-10-02:
  - "Latest fetch that has events": staging holds rows only for fetches with events, so the
    latest staging fetch of a match is that fetch; a later empty fetch keeps the earlier list.
  - The descriptions of base and the fact (persisted to BigQuery) and layering.md §Materialisation
    are corrected to the new behaviour; the full-rebuild list there gains fct_fixture_event.
  - Checked before building, approved by the CPO in chat, 2026-10-05: in the four matches whose
    older fetch holds extra goals, the latest fetch's goals equal the official score and the
    extra goals do not. Two penalty shoot-outs (23 kick events) exist only in older fetches and
    leave the fact; both readers of shoot-out kicks only exclude them, and the result stays in
    fct_fixture.
  - assert_no_event_loss_since_cutoff and its event_loss_detector_from var are deleted: with the
    fact rebuilt from base, the fact can no longer hold an event base lacks, so the test cannot fail.
  - The deleted comments carried three issue numbers, so the comment-history pin in
    tests/test_no_decision_history_in_code.py is lowered to the measured count.
  - Every other place that states the old per-position rule or the incremental load is corrected:
    docs/data_contract.md "Fixture details" (the owner of "raw keeps both versions, base
    decides"), the staging description (persisted), the comment in batch_fixtures.py (comment only;
    it also loses a quoted phrase and a pointer to the deleted escalations log), a test docstring,
    and the header of assert_fanout_facts_not_empty.sql.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: the new test and the fact's full
  rebuild, measured by dry run below the incremental load they replace; numbers in the MR head.

decisions_reserved:
  - None.

done_when:
  - The MR data build passes, including the new test; measured on the MR build's datasets: no
    event beyond the latest fetch, and only the 8 matches differ from prod.
  - pytest (whole suite), ruff, SQLFluff and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
