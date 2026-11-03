# Task contract — hooks judge the worktree the action targets

objective: >
  The governance hooks find the repository from the target of each action instead of from
  CLAUDE_PROJECT_DIR: an edit's own file, a shell command's working directory. A session working
  in a git worktree is then judged against that worktree's contract, review and staged diff.
  CLAUDE_PROJECT_DIR stays the fallback when the target resolves to no worktree.

refs: >
  #34 and #59, approved in chat, 2026-11-03.

scope_paths:
  - .claude/hooks/_command_utils.py
  - .claude/hooks/task_contract_gate.py
  - .claude/hooks/stop_gate.py
  - .claude/hooks/git_discipline.py
  - .claude/hooks/comment_history_gate.py
  - .claude/hooks/sentence_length_gate.py
  - .claude/hooks/host_fingerprint_gate.py
  - .claude/hooks/tracker_snapshot_gate.py
  - tests/test_hooks_resolve_worktree.py
  - docs/agent_guardrails.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Approved in chat, 2026-11-03: the CPO approved fixing #34 and #59 in one MR, editing the
  hooks under .claude/hooks/ listed in scope_paths, routed to cto-reviewer and platform-reviewer.

impact_map: >
  fires_on: task_contract_gate.py on every PreToolUse Edit/Write/MultiEdit/NotebookEdit, Bash and
  Artifact event and every PostToolUse Bash event; git_discipline.py on every PreToolUse Bash
  event, its commit gate on `git commit`; stop_gate.py on Stop; comment_history_gate.py,
  sentence_length_gate.py, host_fingerprint_gate.py and tracker_snapshot_gate.py on PreToolUse
  edits. All are registered in .claude/settings.json, which does not change.
  imports: stop_gate.py imports `_repo_root`, `_read_contract`, `_dirty_outside_task_dir`,
  `_matches_scope` and `_is_protected` from task_contract_gate.py; scripts/check_task_artifacts.py
  imports git_discipline.py and task_contract_gate.py for the CI recompute and passes its own root,
  so CI is unaffected. Every hook imports `_command_utils.py`; the two new helpers are additive.
  what_changes: each hook's root comes from `git rev-parse --show-toplevel` at the target when
  the target is in a worktree of the same repository as CLAUDE_PROJECT_DIR. Any other target
  inside CLAUDE_PROJECT_DIR (no repository, a nested foreign `.git`, inside `.git/`) is judged by
  the existing `_repo_root()`, as today; any other target outside it is not judged, as today.
  stop_gate.py runs the gates with the resolved worktree's `.venv`, else the main checkout's
  (the parent of `git rev-parse --git-common-dir`), else its own interpreter.
  stops_being_enforced_if_wrong: a resolver that returns None too eagerly would silently stop the
  contract gate and the commit gate for work inside the repo. The tests pin an edit inside the
  main checkout judged exactly as before, and both directions of the worktree case.
  on_failure: every hook keeps failing open; a git error falls back to the old root, never to
  no judgment.

decisions_taken: >
  The approved plan: a shared resolver in _command_utils.py; the contract, stop and commit gates
  and the four edit-time gates use it; `--staged-hash` and `--review-patch` resolve from the
  caller's working directory. Not changed: memory_budget_gate.py (CLAUDE_PROJECT_DIR only picks
  its `--report` default folder), handover_in.py (it only places the SessionStart cache),
  .claude/settings.json. A same-repository check keeps files in other git repositories unjudged,
  as they are today. A Bash command is resolved from the event's `cwd`; a leading `cd X &&` inside
  the command is not parsed. Cost: one or two `git rev-parse` calls per hook run.
  THRESHOLD: a guard invariant changes. An action in a worktree of this repository is judged by
  that worktree's contract, review and staged diff instead of CLAUDE_PROJECT_DIR's; where the
  worktree's contract is wider, the action is allowed there. Every target that is not in such a
  worktree is judged exactly as before. The cto-reviewer rules on it.

decisions_reserved:
  - none: the plan is CPO-approved, approved in chat, 2026-11-03, and no page output changes

done_when:
  - tests/test_hooks_resolve_worktree.py passes; its worktree tests fail against main's hooks
  - the full pytest suite and the offline gates pass
  - required reviewers PASS; review.md bound to the staged diff

amendments:
  - 2026-11-03: stop_gate.py takes `.venv` from the resolved worktree, else the main checkout,
    with a test for a worktree without `.venv` — authority: approved in chat, 2026-11-03.
  - 2026-11-03: a target inside CLAUDE_PROJECT_DIR that is not in a worktree of this repository
    is judged by the fallback, with a test for `git init` over a protected folder — authority:
    the cto-reviewer's round-1 finding; it narrows the change to the approved plan.
