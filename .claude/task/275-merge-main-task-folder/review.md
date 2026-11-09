# Review — fix/275-merge-main-task-folder — 2026-11-09

diff_sha256: a9fc67556963c003e6efd702ffb9bcbacb8393c095d8afabea80e69d52025e26

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the contract is unchanged across both rounds; amendments are (none).
- protected_override names a dated approval in the task's own session; impact_map traces the real callers of both hooks.
- No new mechanism, service, dependency, run or cost; decisions_taken records the merge-base rule and RECURRING COST: none.
- Round 2 delta: the unresolved-base refusal fails closed and adds no product text; the test parametrization widens coverage only.
- Doc-sync: no document describes the merge-time base; approved_design `none` holds.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Hooks still fail open on exceptions: `merge_heads` and `_merge_result_paths` catch git and OS errors; `_staged_paths` falls back to index-vs-HEAD.
- CI fail-closed untouched: check_task_artifacts.py passes an explicit base and has no MERGE_HEAD, so it takes the unchanged path.
- Review hash stays content identity: the merge-time base is an ancestor of main, and the hash equals CI's `main...HEAD` recompute after the merge commit.
- Outside a merge, both `merge-base` calls only swap two symmetric arguments; every value is byte-identical to before.
- Round 2 delta: during a merge with an unresolvable base, `task_folder` refuses with a way out (fetch, GOVERNANCE_BASE, abort) instead of adopting main's incoming folder; no workflow lock.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the ref-loop base, the explicit-base merge path, the unresolved-base fallback and a linked worktree were unpinned, and one git call was unguarded. Round 2: all pinned by the parametrized test, the call is guarded; findings closed.
- Linked worktree: MERGE_HEAD is read from the worktree's own git dir through `--git-path`; the variant passes only if that read works.
- Reverting any changed branch (`_base_commit` either path, `_staged_paths`, `task_folder`, `_dirty_outside_task_dir`) fails an assertion.
- Stop hook mid-merge counts the branch's paths only, so it no longer tells the agent to revert main's incoming files.
- Not pinned, low severity: `_staged_paths` falling back when `_base_commit` raises mid-merge; it demands more review, never less.

## escalations
(none)
