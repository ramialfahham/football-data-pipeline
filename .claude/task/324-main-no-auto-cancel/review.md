# Review — claude/324-main-no-auto-cancel — 2026-11-16

diff_sha256: 365479d5cf16a3d5b1a00de0818624293edd43a3e0c367e4f00cfb29bb5f6ac8

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Checked the diff's paths against scope_paths: only .gitlab-ci.yml, tests/test_governance_hooks.py and the task folder, all in scope; no amendments.
- Checked the change against the §10 classes: one key on an existing workflow rule, no new mechanism, job, cadence, metric or wording.
- Checked protected_override and impact_map on the protected path: both present and filled; approved_design "none" is honest, no page surface touched.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Checked guard authority on .gitlab-ci.yml: protected_override names the approval in the house form and the impact_map covers writers, downstream, deploy order and blast radius.
- Checked the guard invariants: the key only stops GitLab cancelling main pipelines; MR pipelines keep the default; .not_on_schedule and the schedule clause are untouched.
- Checked recurring cost: no new run; a merge whose pipeline was cancelled now runs the build its own changes: filters select, and prod writers still queue on the prod-warehouse-write resource group.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Checked the syntax at .gitlab-ci.yml lines 49-51: auto_cancel: on_new_commit: none is valid under workflow:rules; nothing in the file sets interruptible or another auto_cancel.
- Checked coverage by first-match: MR pipelines match the merge_request_event rule and keep conservative; push, web and schedule on main match the main rule and get none.
- Checked the test fails on revert (on_new_commit is None for push_main) and on moving the key to workflow level (the mr assertion fails); an unknown condition or no matching rule raises.

## escalations
(none)
