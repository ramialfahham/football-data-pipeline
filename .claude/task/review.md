# Review — fix/facts-rebuilt-in-full — both stat facts rebuilt in full every night; the match-stats table shows every line the provider sent

diff_sha256: b29829bb1ad822e5f3ed4e4f0d0b89c45092171ce1adef3626c37b61a2baa455

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed path is in scope_paths; shared_columns.md and the verify-competition-ingest skill came in by recorded amendments with their reasons.
- Authority: the rebuild, the equality test, the has_stat_line column and the mart's rows rest on the CPO's two quoted approvals of 2026-10-03; the four readings rest on the dated delegation and the diff implements each as stated.
- layering.md: the edit removes the two facts from the incremental exception and records an approved decision; it extends no rule, and fct_fixture_event keeps the exception.
- Reserved items, mechanism and cost: nothing reserved is decided; no new library, service, hook or step; the recurring cost is declared and owed to the CPO before the merge.
- Round 2: the skill edit is doc-sync to the approved decision, not a §10 class; no secret or permission change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: has_stat_line is derived in base from the delivered line before the blank rule fills it; the two facts only select from base; fct_fixture_event keeps its config.
- History: staging reads every raw row and base keeps the latest per key, so a rebuild equals the merge on current data; the player base has no filter that drops rows.
- The equality test lists exactly the columns each fact takes from base (35 player, 20 team), leaves out the derived is_starter and keys, compares both ways, and every compared type is safe for EXCEPT DISTINCT.
- Readers of the removed config and tests: none left; assert_fanout_facts_not_empty and the CI selectors still hold.
- Round 2: the skill's check-3 row and its stale-row note now match the script's hint and are true of fct_fixture_team_stats and fct_standings.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The switch from incremental to table is one create or replace per fact: an interrupted build leaves the old fact in place, and a rerun is idempotent.
- Leftover __dbt_tmp relations expire and are skipped by the cleanup script; a table build never reads one.
- Nothing in CI, the nightly entrypoint, the runbook or scripts depends on the facts being incremental.
- The new test's Jinja renders the same column order on both sides, fails closed on a missing column, and runs once per nightly and twice per post-merge build.
- No dependency, credential, workflow or hosting change.

## escalations
(none)
