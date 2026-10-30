# Review — feat/235-table-exact — 2026-10-30

diff_sha256: 44897037f13515842184f25b197333e00a1fd4b32e767b9f2310f779938c375d

rounds: 7

rounds_cap_override: the first two MR data builds failed the published-table test on places; the fourth and fifth rounds review the fixes, approved in chat, 2026-10-29; the sixth reviews the Portuguese head-to-head condition the league's 2025-26 tables showed, approved in chat, 2026-10-30; the seventh reviews the official goals of a Copa del Rey match that failed main's build, approved in chat, 2026-10-30

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged path is in scope_paths; fixture_goal_corrections.csv enters scope by an amendment that names its approval; nothing credential-shaped.
- No new mechanism: the seed is the documented route for a match whose goal events stay wrong; six data rows only.
- The rows correct the failing match from its official match sheet rather than weakening the test.
- Both head-to-head passes keep the equal-meetings condition reviewed in round 6.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The six rows match the seed header and tests: unique fixture and goal order, team and detail present, source_kind official, an https source; CRLF and quoting as the existing rows.
- For a corrected match the base model replaces the provider goals with the seed goals, so the match serves 1-5 and assert_result_corrections_applied stays clean.
- The match now has every goal with its minute in chronological order, so goal_data_state is goals and assert_mart_competition_fixtures_goals_add_up has nothing to report for it.
- is_met_equally is true exactly when every pair of level teams has met once or every pair twice, in both head-to-head passes, with no fan-out.

## escalations
(none)
