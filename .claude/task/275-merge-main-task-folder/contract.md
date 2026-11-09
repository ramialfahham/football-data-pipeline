# Task contract — a branch that merges main into itself passes the task-folder gate

objective: >
  Issue #275. While a merge from main is in progress, the local gates count the branch's paths and
  the review hash from the merge-base of main with the merge result, so main's merged task folders
  never count as the branch's and the branch can be edited and committed with no rewrite.

refs: >
  #275, approved in chat 2026-11-09 (plan and protected-path go).

scope_paths:
  - .claude/task/275-merge-main-task-folder/
  - .claude/hooks/git_discipline.py
  - .claude/hooks/task_contract_gate.py
  - tests/test_task_folders.py

protected_override: >
  Approved in chat, 2026-11-09: the CPO approved the plan and the edits to
  .claude/hooks/git_discipline.py and .claude/hooks/task_contract_gate.py in this task's own session.

impact_map: >
  git_discipline.py: fires PreToolUse Bash on every git command. `_base_commit` feeds the review
  hash (`_staged_diff_bytes`), the reviewers' patch (`--review-patch`), `--staged-hash` and
  task_contract_gate's `_committed_paths`; `_staged_paths` feeds the commit gate's reviewer routing
  and acceptance trigger. Imported by scripts/check_task_artifacts.py for `_rounds_gate` only, so
  CI's base and hash are untouched. The change applies only while `MERGE_HEAD` exists; outside a
  merge every value is computed as today. If wrong during a merge: the hash disagrees with CI (CI
  fails closed) or the gate denies (fail closed); an exception fails open by house rule and CI is
  the backstop.
  task_contract_gate.py: fires PreToolUse Edit|Write|MultiEdit|NotebookEdit|Bash|Artifact and
  PostToolUse Bash. `task_folder` is read by the edit gate, the commit gate, stop_gate.py and
  check_task_artifacts.py (CI passes an explicit base and has no merge in progress, so its path is
  unchanged). If wrong during a merge, `task_folder` returns no folder and edits are denied (fail
  closed), as today.
  CI: no .gitlab-ci.yml or script change; validate:governance already diffs base...HEAD.

approved_design:
  - none: no page output changes; the diff touches no site_v2/src/ file or export script

decisions_taken: >
  The base during a merge is `git merge-base <main> HEAD MERGE_HEAD`, the commit CI diffs from once
  the merge is committed. During a merge the branch's paths are the index, working tree and
  untracked files compared with that base. RECURRING COST: none.

decisions_reserved:
  - none: the plan and the protected-path edits were approved in chat 2026-11-09

done_when:
  - .venv/Scripts/python.exe -m pytest tests/ -q passes.
  - tests/test_task_folders.py pins a branch that merges main, with another task's folder on main, through a conflict: edits allowed, commit gate passes, --staged-hash equals CI's recompute, and check_task_artifacts.py passes after the merge commit.

amendments: (none)
