# Task contract — handover: block-audit method, automation note, home-page status

objective: >
  Update `.claude/active_work.md` to reflect current state before this chat ends (context nearly
  exhausted, continuing in a fresh session). Bookkeeping only.
refs: this session's work in full — !72 (shared ordering), !73+!74 (Top players ruling), #78 (the
  filed follow-up sweep).

scope_paths:
  - .claude/active_work.md
  - .gitlab-ci.yml
  - deploy/nightly/README.md
  - tests/test_governance_hooks.py
  - .dockerignore
  - .gcloudignore
  - Dockerfile

amendments:
  - 2026-08-18: + `.gitlab-ci.yml`, `deploy/nightly/README.md`, `tests/test_governance_hooks.py`,
    `.dockerignore`, `.gcloudignore`, `Dockerfile` — authority: CPO, "merge conflict" (this
    session), the same standing instruction #74's own contract cites as covering conflict
    resolution as `main` moves. NOT new work from this task. `main` moved with
    `fix/74-nightly-image-tracks-main` (MR !70, merge commit 254415b) while this branch's MR (!75)
    was open; merging `main` in to resolve the conflict brings in #74's already-built,
    already-reviewed (cto-reviewer + platform-reviewer, opus, multiple rounds per its own
    `review.md`) and already-merged content. None of it is authored, edited, or re-verified by
    this task — named here only so the scope gate, which does not distinguish a merge from new
    authorship (the same gap `active_work.md`'s OWED section already logs), has something to
    check against.

impact_map: >
  writers: none. downstream: this IS the continuity mechanism for the next session — its accuracy
  is the point. layer_rules: not applicable. blast_radius: one file authored (`active_work.md`);
  six more arrive unchanged via the `main` merge (see amendments).

decisions_taken: none — recording, not deciding.
decisions_reserved: everything substantive; this is bookkeeping.
done_when: active_work.md reflects current state, under 16,000 characters, and is committed.
