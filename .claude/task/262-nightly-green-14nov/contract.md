# Task contract — the two defects that failed the 14 Nov nightly, fixed at their source

objective: >
  Issue #262: the 14 Nov nightly failed four error tests, and dbt skipped every model downstream of
  the three models they test, so the marts did not refresh. (1) not_null on fct_fixture's
  shootout_home, shootout_away and winner_team_sk: the provider files Coupe de France fixture 1647959
  (La Neuvillette 2-2 Valenciennes, 13 Nov 2026) as settled on penalties with no shoot-out score. One
  fixture_result_corrections row gives the shoot-out, 0-3, from two match reports.
  (2) assert_player_stat_corrections_within_limit: CONCACAF Nations League 2025 reached 8.7%
  corrected player rows against the 8% limit, because the provider's first fetch of its 12-14 Nov
  matches holds 2 to 9 stat lines per team and card events for players it holds no stat line or id
  for, so the cleaning blanks those matches' cards. The provider completes such player stats days
  later, and the data contract counts a match's player stats as not final until its second fetch.
  The test measures the matches whose player stats are final, as that rule says. Each fix's data
  build fails on the other's test, so one MR carries both.

refs: >
  #262; routes ruled by the coordinating session on 2026-11-14: the provider's data is wrong by
  default; the shoot-out is researched (never rfef.es) and corrected through the existing route in
  base; the over-limit share is measured on final player stats under docs/data_contract.md "Second
  fetch", with the limit and the severity unchanged and a named case.

scope_paths:
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/tests/assert_player_stat_corrections_within_limit.sql
  - .claude/task/262-nightly-green-14nov/contract.md
  - .claude/task/262-nightly-green-14nov/review.md
  - .claude/task/262-nightly-green-14nov/review_input.patch

approved_design:
  - none: no page layout changes; fixture 1647959 shows Valenciennes winning 3-0 on penalties

decisions_taken: >
  Ruled by the coordinating session on 2026-11-14. (1) Fixture 1647959's shoot-out is 0-3: Footeo's
  Coupe de France round-up and Sport Club Reims' match report agree on 2-2 and 0-3 on penalties, and
  the match_reports kind takes two sites. The provider's 2-2 stays; base derives the winner from the
  shoot-out, so winner_team_sk becomes Valenciennes (105). (2) The limit test measures a match once
  its player stats are final: its latest fetch came 72 hours or more after kickoff, the ingestion's
  second_fetch_due rule (SECOND_FETCH_DELAY, 3 days). The latest fetch is the newest raw_ingested_at
  of the match in any of the four staging models of the fixture-details bundle (player stats,
  lineups, events, statistics), so a second fetch whose player stats came back empty still counts.
  A match with no fetch or no kickoff is measured. Measured on prod 2026-11-14, read-only: of 49,846 matches with player stats, the 31
  kicked off 12-14 Nov wait for their second fetch and no older match does. The limit stays 8% and
  the severity error. The named case, Aruba-Antigua and Barbuda (fixture 1639932, 23 Sep 2026,
  fetched again on 6 Oct), pins that a final match is measured.

decisions_reserved:
  - The Nations League's Sep-Oct matches whose cards stay blanked: under the limit, researched in their own task.

done_when:
  - dbt parse passes; sqlfluff lint passes on the changed test.
  - The full pytest suite passes.
  - The MR's data build passes not_null_fct_fixture_shootout_home, not_null_fct_fixture_shootout_away, not_null_fct_fixture_winner_team_sk, assert_result_corrections_applied and assert_player_stat_corrections_within_limit; compared with prod, fixture 1647959's shoot-out and winner are the only model change.
