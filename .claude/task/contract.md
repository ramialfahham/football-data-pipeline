# Task contract — the tracker backup stays on this machine

objective: >
  `docs/tracker/gitlab_snapshot.md` copies every GitLab issue's text into the public repository,
  while issues are now visible to project members only. Untrack it and gitignore `docs/tracker/`;
  the backup stays on this machine.

refs: >
  #199 (how-we-work documents).

scope_paths:
  - docs/tracker/**
  - .gitignore
  - tests/test_tracker_snapshot.py
  - scripts/snapshot_tracker.py
  - CLAUDE.md
  - docs/agent_guardrails.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  Approved by the CPO in chat, 2026-10-05: the backup local-only, with the CLAUDE.md and
  agent_guardrails.md text shown to him. Readings, under the delegation of 2026-10-02:
  - The two checksum tests skip when the file is absent: CI never has it.
  - scripts/snapshot_tracker.py: its docstring's lines on CI and on riding the next commit are
    corrected to the gitignored file.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - `git ls-files docs/tracker` is empty and the local file stays; pytest (whole suite), ruff and
    the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
