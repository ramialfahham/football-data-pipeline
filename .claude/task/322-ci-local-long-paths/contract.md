# Task contract — ci_local.py long paths on Windows

objective: >
  Issue 322: scripts/ci_local.py must hand a job's artifacts to the next job, and remove its run
  folders, when a path exceeds 260 characters on Windows, so the command runs from a deep worktree.

refs: >
  Issue 322. Found by the issue 316 session. Requested by the coordinating session.

scope_paths:
  - scripts/ci_local.py
  - tests/test_ci_local.py
  - .claude/task/322-ci-local-long-paths/contract.md
  - .claude/task/322-ci-local-long-paths/review.md
  - .claude/task/322-ci-local-long-paths/review_input.patch

depends_on:
  - none: starts from gitlab/main after the merge of the MR that added the command

shared_files:
  - none: no design baseline, chart manifest or chart pin is touched

decisions_taken: >
  The fix lives in the script and changes no machine setting. Rests on the task brief from the
  coordinating session, 16 Nov 2026. No new mechanism, no new dependency, no recurring cost.

decisions_reserved:
  - none: an engineering fix inside the local CI command; no page, metric or name is decided

done_when:
  - a test that builds an artifact tree deeper than 260 characters fails before the fix and passes after
  - python -m pytest tests/test_ci_local.py passes
  - python scripts/ci_local.py --mr from a worktree under .claude/worktrees runs validate:ui to the end

amendments: (none)
