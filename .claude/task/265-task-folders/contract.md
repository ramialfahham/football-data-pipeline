# Task contract — each task writes to its own folder

objective: >
  Issue #265. Each task writes its contract, review and evidence files to `.claude/task/<issue>-<slug>/`
  instead of the shared `.claude/task/`, so several MRs can be open at once and merge in any order.

refs: >
  #265, approved in chat 2026-11-07 (plan and protected-path go).

scope_paths:
  - .claude/task/265-task-folders/
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/TEMPLATE.md
  - .claude/hooks/task_contract_gate.py
  - .claude/hooks/git_discipline.py
  - .claude/hooks/stop_gate.py
  - .claude/review_routing.json
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/agents/platform-reviewer.md
  - .claude/agents/scope-auditor.md
  - .claude/agents/seo-expert-reviewer.md
  - scripts/check_task_artifacts.py
  - scripts/report_process_health.py
  - tests/test_task_folders.py
  - tests/test_governance_hooks.py
  - tests/test_hooks_resolve_worktree.py
  - tests/test_governance_doc_parity.py
  - docs/working_agreement.md
  - docs/agent_guardrails.md

protected_override: >
  Approved in chat, 2026-11-07: the CPO approved the plan and then typed the go for the protected
  paths in this task's own session (hooks, review routing, reviewer briefs).

impact_map: >
  task_contract_gate.py: fires PreToolUse Edit|Write|MultiEdit|NotebookEdit|Bash|Artifact and
  PostToolUse Bash (.claude/settings.json). Imported by stop_gate.py (_read_contract,
  _dirty_outside_task_dir, _matches_scope, _is_protected), by scripts/check_task_artifacts.py
  (_read_contract, _is_page_surface, unapproved_designs, default_base_ref) and by
  tests/test_governance_hooks.py. If the resolver is wrong, _read_contract returns None and every
  in-repo edit is denied (fail closed for edits), or it returns another task's contract and the
  scope check reads the wrong allowlist. On an exception the hook fails open (house rule); the
  commit gate and CI are the backstops.
  git_discipline.py: fires PreToolUse Bash on every git command; the commit gate reads review.md,
  the contract's acceptance_criteria and acceptance_evidence.md. Imported by check_task_artifacts.py
  (_rounds_gate). If the folder is wrong, the commit gate reads no review.md and denies (fail
  closed). The review hash (_staged_diff_bytes) is unchanged; only its exclusion list moves to
  per-folder patterns, which select the same paths on an unchanged diff.
  stop_gate.py: Stop hook; reads the contract through _read_contract, so it follows the resolver.
  review_routing.json: read by git_discipline (artifact_only, hash and review exclusions, routing)
  and check_task_artifacts.py. A wrong exclusion pattern changes the review hash (CI and local
  compute it from the same list, so they still agree) or hides/shows a file to reviewers.
  test_every_task_artifact_is_classified pins the review exclusions.
  agents/*.md: prompts only; they name where the patch and contract are read.
  CI: validate:governance runs check_task_artifacts.py with --base origin/<target>; no
  .gitlab-ci.yml change. Branches still on the old layout fail CI after this merges (no task
  folder), which is fail closed and forces the replay step.

approved_design:
  - none: no page output changes; the diff touches no site_v2/src/ file or export script

decisions_taken: >
  NEW MECHANISM: per-task artifact folders, approved in chat 2026-11-07 (plan approved, then the
  typed go for protected paths). Folder name `<issue>-<slug>` was left to the builder by the
  coordinating session's brief. A merged task's folder stays in place and later branches may not
  touch it. No compatibility path for the old layout: branches still on it when this merges replay
  once into their own folder. RECURRING COST: none (no new run, no new reviewer row).

decisions_reserved:
  - When this MR merges relative to the queued Player page, term list and comment sweep MRs is the
    coordinating session's call; the recommendation is after them, so they need no migration.

done_when:
  - .venv/Scripts/python.exe -m pytest tests/ -q passes.
  - tests/test_task_folders.py pins two tasks side by side, a missing folder and another task's folder.
  - python scripts/check_task_artifacts.py resolves 265-task-folders and passes after the review lock.
  - An Edit to .claude/task/999-other/x.md in this worktree is denied by the live hook.

amendments: (none)
