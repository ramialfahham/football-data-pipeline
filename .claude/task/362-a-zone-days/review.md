# Review — claude/362-a-zone-days — 2026-11-27

diff_sha256: 8bc4c63aac7b074a3b5bee9579d47a1ec52a69e1f26ae4fa1fde2ced34b3c04d

rounds: 4
rounds_cap_override: approved in chat, 27 Nov 2026

## analytics-engineer-reviewer
VERDICT: PASS
findings:
risks_checked:
- Searched the callers of shape_next_match, _competition_fixture, shape_match_day_payloads and fetch_fixture_payloads and their test rows for the keys read strictly: no gap left.
- Reach test: wrong_day_facts reads every mart row with no is_utc_day filter, compares previous_day, next_day and is_opening_day with expected_days, and fails a served day that is not expected. expected_days is still recomputed from fct_fixture and int_legs__team_match.
- Reach test: out_of_reach compares only UTC-day rows, in both directions, and keeps the unplayed-fixture check. A fixture with no UTC-day row fails the zone-day test.
- The mart_match_days descriptions and header match the SQL, and no other stale wording is left in dbt_project.
- The order claim is limited to a round, or a list across competitions, which is what the order test checks.
- deploy_order names both early-deploy hazards and fdp-site, matching the site image paths in .gitlab-ci.yml.
- The fix diff changes no model SQL logic, export code, seed or project config. Read-only review: no pytest, dbt, SQLFluff or BigQuery was run by the reviewer.

## platform-reviewer
VERDICT: PASS
findings:
risks_checked:
- tests/test_kickoff_clock_146.py carries kickoff_order, shape_next_match still reads it strictly, and the file is in scope with an amendment line. Traced statically.
- No other caller of shape_next_match or of the two next-match queries lacks the column.
- Reverting the kickoff_order line in shape_next_match still fails test_shape_next_match_is_the_mart_row_unless_it_is_this_match.
- deploy_order wording checked against .gitlab-ci.yml: deploy:site-image only updates the job's image and does not run it. Live Cloud Scheduler state not read.
- Reworked reach test: both union branches give the same columns in the same order; it only reads data, so a rerun or an interrupted run leaves nothing to repair.
- The two rewritten column descriptions are under the 1,024-character limit.
- The fix diff touches no hook, workflow, CI file, dependency file, credential, permission or hosting config.

## fixes
- test fixture lacks a newly required column | sweep: grep over tests/ for shape_next_match, group_upcoming_fixtures, shape_match_day_payloads, kickoff_order and is_utc_day | test: tests/test_kickoff_clock_146.py::test_a_next_match_and_a_landing_group_carry_the_clock
- guard narrowed | sweep: every column the reach test compares, checked for the rows it reads; mutants of previous_day, next_day and is_opening_day off the UTC day, run read-only on prod data, each return rows | test: dbt_project/tests/assert_mart_match_days_is_the_matches_page_reach.sql
- unpinned is_utc_day | sweep: every place the export reads or selects is_utc_day | test: tests/test_export_matches.py::test_a_row_without_the_day_flag_stops_the_export
- unpinned kick-off order | sweep: both orders mart_competition_fixtures serves | test: dbt_project/tests/assert_competition_fixtures_orders_follow_the_kickoff.sql

## escalations
(none)
