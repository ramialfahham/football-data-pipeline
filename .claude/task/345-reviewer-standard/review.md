# Review — claude/345-reviewer-standard-eb92fa — 2026-11-24

diff_sha256: 3b08df155b66c45ed251ba77c174b3aca1f3865a31b798b57921c5c1aa10605e

rounds: 3

## scope-auditor
VERDICT: PASS
findings:
- [nit] unverifiable carve-out: _findings_gate none branch, working_agreement.md §2, REVIEW_TEMPLATE.md - a `none:` entry after a FAIL cannot be told apart by the gate
risks_checked:
- Round 1 blocking finding (a fix test that is not a test) is fixed: TEST_PATH_RE refuses contract.md, docs and source files; every place that promises a test file names the same locations.
- Round 3 delta: the site node-test location is declared in decisions_taken and recorded by the third amendment; no new paths, mechanism, cost, credentials or page output.
- Scope, protected_override, impact_map, doc-sync and the §10 sentences beyond the issue's words were checked in round 1; all are listed in decisions_taken.

## cto-reviewer
VERDICT: PASS
findings:
- [nit] none-rule wording: working_agreement.md §2, REVIEW_TEMPLATE.md, AC7 - "followed only PASS verdicts" does not name a round after an answered ESCALATE
risks_checked:
- Round 1 finding (the fixes gate keyed on the round count) is fixed by the lone `none: <why>` entry, swept through the gate, §2, the template, the CI docstring and AC7.
- Round 2 finding (the fix-test locations left out the site node tests, and the sentence was undeclared) is fixed: three locations everywhere, declared in decisions_taken, pinned by a test that fails on the old regex.
- Guard direction unchanged: the hook fails open, CI fails closed; no new dependency, cost, credential or mechanism.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings fixed: the branch-membership condition and the finding separator are pinned by tests (mutation checks fail without them); TEST_PATH_RE narrows the fix test to a test location.
- Round 2 finding fixed: TEST_PATH_RE accepts site_v2 node tests; a glob sweep across the repo found no other test location.
- Hook and CI call the one shared _findings_gate; re-runs are read-only.

## fixes
- fix test accepts any changed file | sweep: grep for every statement of the fix-test rule in git_discipline.py, check_task_artifacts.py, working_agreement.md, REVIEW_TEMPLATE.md and the contract | test: tests/test_reviewer_standard.py::test_a_fix_naming_a_file_that_is_not_a_test_is_refused
- gate condition no test pins | sweep: each condition of _findings_gate removed in turn and the suite run (mutation check) | test: tests/test_reviewer_standard.py::test_a_fix_test_the_branch_does_not_change_is_refused
- fixes gate keyed on the round count | sweep: grep for every statement of the rounds-above-1 rule in the gate, its message, §2, the template, the CI docstring and AC7 | test: tests/test_reviewer_standard.py::test_a_round_after_a_pass_commits_with_a_none_entry
- test locations leave out the site node tests | sweep: git ls-files filtered on test and grouped by folder | test: tests/test_reviewer_standard.py::test_every_test_location_the_repo_runs_is_a_fix_test

## escalations
(none)
