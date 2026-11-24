# Review - claude/37-squads-complete-read

diff_sha256: 523b6049a3658e3bc2d82d0cddf29928359644fb4e0b20913d7f4647789c5687

rounds: 4
rounds_cap_override: round 4 approved in chat, 2026-11-23, recorded as a note on !533; no fifth round

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: no decisions_taken block, an impact_map that listed 13 models as 12 without evidence, and a data_contract.md sentence that gave a rationale inside a definition. Round 2 FAIL: the layering.md edit extended the accumulation class inside the sentence that cites the 2026-06-15 ruling, an ambiguous "This" in data_contract.md, and a "because" clause. Round 3 PASS: the layering.md edit is gone, decisions_taken argues that squads falls under the rule's own unchanged test through the catch-up loader, the invariant sentence precedes the squads sentence, and the "because" clause is removed.
- Every changed path is in scope_paths. No secrets, no workflow change, no site_v2 or export change.
- Residual, not a defect: the in-season path re-fetches every run, so the class argument rests on the catch-up path alone; decisions_taken states it.
- Round 4 PASS (delta): BigQuery rejected the correlated override macro in the join predicate of assert_squads_read_per_team.sql; it now runs in a CTE and the join compares plain columns. The test's meaning is unchanged and nothing else in the diff moved.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement of stg_apif__squads (reads every row, flatten only), base_apif__squads (newest block per team after the team-id override, player grain) and int_player__page_profile (reads base only) checked against layering.md, no defect.
- A team whose newest fetch is empty keeps no older list: the left joins keep the empty block as a row with no player, newest is computed over those rows, src filters the null player after the join.
- assert_player_page_choices_follow_the_rule changes in step with the model; national_seasons is still used elsewhere in that test.
- Round 4 PASS (delta): the test's `staged` CTE matches base's `src`, `expected` selects the same pairs as base, and no correlated subquery remains in a join predicate in the changed models and tests. A dry-run of the compiled SQL passed (1.17 GB, not run).

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: no test drove run_player_squads_catchup, so restoring the discard and require_complete=True at that call site stayed green. Round 2 PASS: test_the_catchup_runner_writes_the_teams_a_quota_cut_reached reaches the real call site and goes red on both revert shapes (parameter restored, or only the call site restored).
- The SQL pins in tests/test_squads_read_per_team.py go red when the qualify, a left join unnest, the newest-block join or a league join in a reader comes back.
- tests/test_staging_key_tests_moved.py: the two reads of stg_apif__squads in base are pinned; the new singular test is exempt with a read count of 3.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Loader: append only, no truncate; a quota cut writes the teams fetched and captured_team_seasons does not list the rest, so the next run fetches them; no duplicate of a written team; the cut is still reported once through the quota flag.
- Completeness gate reads latest row per league from full-mode comps only, so catch-up subset rows never count as a snapshot there. Nightly image carries loader and dbt together, so no old-staging-over-new-rows window.
- data_contract.md lines 77, 85 and 185 match the code; the staging models using the latest-per-league window are exactly the five named.

## escalations
(none)
