# Review — claude/347-statistics-export-b — 2026-11-25

diff_sha256: 06feefa216ff7ecdb4a497f3a6a0935dbfbbae6164fa90b73ea4fefdf905fe57

rounds: 2

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Passed on the unsplit branch in round 1 with the season guard and the order test in the tree. This MR carries exactly that code and those tests: a script confirmed that the diff of each file equals the reviewed patch's diff minus the lines merged in !537 (the two seed lines and the pinned-order lines of tests/test_catalogue_order.py), with no file outside the reviewed patch.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL closed in round 2 on the unsplit branch: a fetch-level catalogue-order test and a loud failure for two current seasons in one league. Both are in this diff, byte-identical to what was passed (script-checked against the reviewed patch); the entity stays outside DEPLOY_ENTITIES.

## fixes
- an export that did not prove it follows the catalogue order and silently wrote two files for a league with two current seasons | sweep: every place the export orders boards or picks the season is in fetch_statistics_payloads, found by reading the export's Statistics functions and grepping metric_order and is_current_season in scripts/export_site_data.py | test: tests/test_statistics_payload.py::test_the_fetched_boards_follow_the_catalogue_order_whatever_order_the_warehouse_serves
- the two-current-seasons guard | sweep: the same grep; the guard sits where the two marts' rows are joined | test: tests/test_statistics_payload.py::test_two_current_seasons_for_one_competition_fail_the_export

## escalations
(none)
