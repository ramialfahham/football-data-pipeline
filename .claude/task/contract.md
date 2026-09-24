# Task contract — Three stale facts in CLAUDE.md

objective: >
  Correct three facts in CLAUDE.md that are wrong today, so none can go stale again: the memory
  location (an old machine's path and two files that do not exist), the CI job list (missing
  jobs), and the Stop hook's gate count (says five, runs six).
refs: >
  No issue: a documentation correction with no new requirement (working_agreement §1 carve-out).
  His go in chat on 2026-09-24, "clean up", to the three stale facts listed in the MR of #163.

scope_paths:
  - CLAUDE.md
  - .claude/task/**
  - docs/tracker/**

decisions_taken: >
  Each fact becomes a pointer to its single source instead of a copy: the memory folder is named
  by its pattern under `~/.claude/projects/`, with `MEMORY.md` as the index; the CI jobs are
  whatever `.gitlab-ci.yml` defines; the Stop hook's gates are `FAST_GATES` in
  `.claude/hooks/stop_gate.py`, run with the repo's `.venv`. No other line changes.
  THRESHOLD DECLARATIONS: no new mechanism, no recurring cost.

decisions_reserved:
  - none open: the three corrections were approved as listed.

done_when:
  - the three passages point at their sources; no other CLAUDE.md line changes
  - `tests/test_no_decision_history_in_docs.py` and the governance tests pass
  - blinded review PASS; MR open; CI green

amendments: (none)
