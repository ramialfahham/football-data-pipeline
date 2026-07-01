# Task contract — handover refresh (post-#615)

> Written on a CLEAN tree (branch chore/handover-refresh-615 off main @ dafd463).
> Bookkeeping only — no code/model/doc-of-record change. Refreshes the handover to the
> post-#615 state and drops the now-resolved content_architecture drift note.
> See docs/working_agreement.md §2 (contract). Handover refreshes skip plan mode (CPO 2026-06-30).

objective: >
  Bring .claude/active_work.md up to date after #615 (content_architecture.md §3/§7 block↔mart
  map reconciled to reality, MERGED, main now @ dafd463). Drop the reserved "content_architecture
  §3 status drifted / needs a reconciliation pass" note — it is RESOLVED by #615. Record the CPO's
  next-track pick (A — Squad screen). No status claim changes beyond removing the now-false drift line.

refs: >
  main @ dafd463 (#615). Prior handover was the #614 version (@ f4b1aa8, up to #613). CPO approved
  this refresh + picked track A (Squad screen) this session (2026-07-01).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only — updates the _Last updated_ header (2026-07-01, main @ dafd463, MERGED #615),
  appends #615 to the "main carries" line, updates the two f4b1aa8 references to dafd463, replaces
  the line-25 drift NOTE with a plain "reconciled by #615" pointer, prepends #615 + #614 to RECENT
  PRs, and refreshes the NEXT list to the four current candidates with the CPO's pick (A — Squad
  screen) recorded. Invents NO product/UX/metric/naming decision.

decisions_reserved:
  - The Squad-screen spec itself (track A) — its own contract + plan-mode task, next.
  - Whether folding a closed gap's spec-sync into its gap PR generalises — still open, CPO call.
  - The two stale-wireframe flags + the wireframe §10 doc-status sweep — separate items, not touched here.

done_when:
  - active_work.md header, "main carries" line, the two f4b1aa8 refs, the line-25 drift note, RECENT
    PRs, and the NEXT list are current (post-#615, track A picked); no other status claim changes.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
