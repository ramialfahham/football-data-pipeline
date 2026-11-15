# Review — claude/314-merged-result-ci-c28460 — 2026-11-15

diff_sha256: dc83deb12dc097eb3c366e111b844953ef8dbc7f38bd97d1f03e6df1d5379621

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file in the patch is in scope_paths; the amendment adding tests/test_sentence_length_in_docs.py names issue 314, and the pin drops 42 to 41 for the one sentence removed from layering.md.
- Each new mechanism (merged-result step, list_mr_scratch.py, gate job, check_sweep_superseded.py, per-MR and per-branch resource groups) is declared in decisions_taken, with the accumulating scratch datasets declared as recurring cost; no delete call exists in the lister.
- Doc-sync: layering.md and operations_guide.md were the only live descriptions of the old scratch name; no product, UX or naming decision is taken.
- Round 2 delta: per-command safe.directory, the alpine gate image and the new tests stay in scope and add no mechanism, cost or credential.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanisms are declared under issue 314; everything uses tools the repo already has.
- check_sweep_superseded.py fails closed: any error exits non-zero and the full sweep runs; no deploy job needs validate:ui.
- The gate job holds no credential and runs one echo; wait_for_nightly.py runs under the existing identity with no new IAM grant.
- No dependency added; per-build BigQuery bytes unchanged (no incremental models); pipeline frequency unchanged.
- Round 2 delta: safe.directory is per command and writes no global config; the alpine image is a container image, not a dependency.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 F1 closed: the shell tests build their environment without MR_TARGET_*, pinned by a test that sets both variables.
- Round 1 F2 closed: main() of check_sweep_superseded.py runs end to end against a temporary origin for both exit codes, and a failed fetch or missing environment never exits 0.
- The merged-result step re-runs safely, unshallows a fetch-strategy folder left at depth 20, and fails on a conflict; validate:ui merges the same target commit through build:site-v2's dotenv report.
- data:build:mr fails closed without the merge step, compiles state and diffs seeds against the merged commit, and the gate's rules equal its own so needs: cannot dangle.
- Every git call in the step carries safe.directory per command; the images ship git 2.39 and 2.43, which honour it from the command line.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- No model, seed, macro or dbt_project.yml change; generate_schema_name is unchanged and the prod target is untouched.
- The seed diff against MR_TARGET_SHA selects exactly the seeds the branch changed, written only to the per-MR scratch dataset.
- state:modified+ compares the merged tree against the exact target commit the step merged; no second fetch exists.
- list_mr_scratch.py parses legacy and new names and never lists prod, dev or ci_mrshared.
- Round 2 delta adds no model, seed, metric or competition identifier.

## escalations
(none)
