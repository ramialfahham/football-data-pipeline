# Review — fix/ci-changed-seed-selection

diff_sha256: 177be476b0c606ad5d9fed2b0a9eebe1ea7c1f5138f3049f7a88ddfb9608700c

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the base-SHA guard sat at the head of a pipe, whose status is the last command's, so a missing base gave an empty selection. Fixed: the git diff is its own assignment ending in `|| exit 1`, and the test pins it.
- Every changed path is in scope_paths; the .gitlab-ci.yml edit stays inside data:build:mr, within protected_override; decisions_reserved untouched.
- The threshold declarations hold: no new mechanism, a per-merge-request cost with its number and nothing on a schedule.
- The CI comment and the test docstring state the mechanism only; no issue, MR, date or chat wording; no secrets.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL on the same fail-open pipe; closed in round 2 without relying on the runner's pipefail.
- Not a new mechanism: one more selector on the existing state:modified+ build, in the same job; no dependency, job, hook or service.
- The data:build:mr guard invariants hold: the per-merge-request target, --defer --favor-state on the build line only, no ingest; no prod writer touched.
- The recurring-cost declaration is adequate: merge request pipelines that change a seed only, measured in the issue.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the test did not pin the `path:` rewrite, the `+` children operator or the unquoted use. Round 2 pins all three, the `|| exit 1`, the absence of a pipe and the line order; each removal fails the test.
- Shell: an unset or unknown base ends the job red; no changed seed leaves today's command; a deleted seed gives a selector that matches nothing without error; the variable survives across script entries.
- YAML: both new lines parse as plain strings (`${f#` and `path:%s` are not comment or key markers).
- dbt 1.7 parses `path:seeds/<file>.csv+` as the path method with children and globs from the project root.

## escalations
(none)
