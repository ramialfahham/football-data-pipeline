# Review — fix/34-hooks-repo-root

diff_sha256: 0aa967ffeb55522656bbc9e353200f212f410ba9a58610ea7f3d1fbba45b273b

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; .claude/settings.json, memory_budget_gate.py and handover_in.py are untouched.
- The guard-invariant change is declared as THRESHOLD in decisions_taken and both amendments name their authority.
- worktree_root returns None only for a target outside CLAUDE_PROJECT_DIR in no worktree of this repository; the nested `git init`, no-repo and `.git/` cases inside it return the fallback.
- The round-3 shell-write fallback change widens judgment only and matches what_changes.
- docs/agent_guardrails.md states current behaviour only; no secrets, no escalations.log entry, no page or dbt surface.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round-1 finding closed: a nested `git init` over a protected folder walks up to the holding worktree and is judged; pinned by test_a_nested_git_init_does_not_exempt_a_protected_folder.
- The declared threshold, an action in a worktree judged by that worktree's contract, is allowed: protected paths still need protected_override, and the commit gate and the CI recompute are unchanged.
- Shell and Edit paths use the same fallback; a write into the main checkout's `.git/` from a worktree is judged, pinned by a test.
- Fail-open holds: git errors return the fallback; the stop gate's `.venv` lookup falls through to its own interpreter.
- No new mechanism, dependency, credential or recurring cost beyond local `git rev-parse` calls.

## platform-reviewer
VERDICT: PASS
risks_checked:
- worktree_root traced case by case: main checkout, nested and sibling worktree, nested foreign repo, unrelated repo outside, `.git/`, and a fallback that is no git repository; the walk always terminates.
- Round-1 findings closed: absolute shell writes resolve their own worktree, and the comment-history, sentence-length and host-fingerprint gates each have a worktree test that fails on main's hooks.
- Round-2 finding closed: the shell-write resolver falls back to `_repo_root()`; test_a_shell_write_into_the_main_git_dir_from_a_worktree_is_judged_by_main pins it.
- Decode errors and ValueError fall back; the stop gate's `.venv` fallback to the main checkout is pinned by a test.
- Commit gate and `--staged-hash` resolve from the same cwd; scripts/check_task_artifacts.py passes its own root, so CI is unaffected.

## escalations
(none)
