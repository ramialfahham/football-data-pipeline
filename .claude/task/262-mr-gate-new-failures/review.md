# Review — claude/mr-gate-new-failures-14f470 — 2026-11-20

diff_sha256: fd074a6d610dd7668ded8b96bf2f2560fb66654bfaf885372fa7adeadab45968

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: all five changed files are inside the contract's scope_paths; amendments is "(none)". No defect.
- protected_override and decisions_taken name the approval as "approved in chat, 2026-11-20", dated and without quoted words. No new mechanism, dependency or recurring cost; the cost goes down.
- Coverage: data:build:main still runs the full singular suite against prod and the nightly entrypoint runs a bare `dbt build --target prod`; new tests pin both and pin the lineage build in data:build:mr. No defect.
- The new layering.md paragraph, the .gitlab-ci.yml comments and the assert_metric_meaning_complete.sql header state the current rule only. No defect.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard weakening is declared and authorised in the contract (protected_override and decisions_taken). The remaining gate, the lineage `dbt build --select state:modified+`, still fails closed and has no allow_failure.
- The full suite still runs where the contract says (data:build:main line with `--select test_type:singular --target prod`; nightly `dbt build --target prod`), verified in the files.
- No new mechanism, dependency or credential change; cost is reduced by about 15.65 GB and 2 minutes per merge request pipeline, declared in the impact_map.
- A change that state:modified does not detect (a dbt var value) skips unchanged-node singular tests on the merge request; they run post-merge. This is the approved rule, not a finding.

## platform-reviewer
VERDICT: PASS
risks_checked:
- data:build:mr still ends in `dbt build`, whose non-zero exit fails the job; the .gcp_auth fail-closed path is untouched.
- "dbt never defers a node it selects" checked against the installed dbt 1.7 merge_from_artifact: a node is deferred only when its unique_id is not in the selected set. The comment in assert_metric_meaning_complete.sql is correct.
- test_the_mr_data_gate_is_its_lineage_build_alone fails when the `dbt test` line is put back or the selector, exclude list or deferral flags change; test_main_and_nightly_builds_run_the_full_singular_suite matches the tree. Known limit: a chained `cd x && dbt test` line would not be seen by the prefix match.
- No remaining reader of the removed step in tests, scripts or hooks; ci_local runs data jobs offline only.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The diff has no model, seed or dbt_project.yml change; no layer-contract rule applies and no competition identifier is hardcoded.
- The removed `dbt test` step is replaced by pins in tests/test_ci_data_job_invariants.py: the lineage build in data:build:mr, and the full singular suite in data:build:main plus the bare `dbt build --target prod` in the nightly entrypoint. Confirmed against the files.
- Coverage after the removal: state:modified+ and the changed-seed path selector still run the tests on modified nodes and their descendants; a change only a var or dbt_project.yml carries is caught post-merge, the cost the contract accepts.
- The rewritten comment in assert_metric_meaning_complete.sql is correct for dbt 1.7.

## escalations
(none)
