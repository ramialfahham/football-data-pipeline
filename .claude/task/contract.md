# Task contract — handover refresh (post-#617)

> Written on a CLEAN tree (branch chore/handover-refresh-617 off main @ 4adafef).
> Bookkeeping only — no code/model/doc-of-record change. Refreshes the handover to the
> post-#617 state: track-A Squad SPEC merged; the GAP-20 wiring PR is the next concrete action.
> See docs/working_agreement.md §2 (contract). Handover refreshes skip plan mode (CPO 2026-06-30).

objective: >
  Bring .claude/active_work.md up to date after #617 (the Team → Squad wireframe spec, MERGED, main
  now @ 4adafef). Record that #391 track A is a two-PR sequence whose SPEC is now done (#617) and whose
  remaining green is the GAP-20 export-wiring PR (mart_roster orphan → wired). Carry forward the two
  reviewer advisories for that wiring PR (omit null-identity members; validate the player_position
  domain before locking GK/DEF/MID/ATT grouping). Also record #616 (the prior handover refresh) merged.

refs: >
  main @ 4adafef (#617 Squad wireframe spec). #616 (handover refresh) merged before it, forcing the
  documented sibling-PR rebase-rebind of #617. CPO merged both. GAP-20 registered in
  docs/wireframes/99_gaps_register.md. New screen: docs/wireframes/11_team_squad.md.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only — updates the _Last updated_ header (2026-07-01, main @ 4adafef, MERGED #617),
  appends #616 + #617 to the "main carries" line + the two f4b1aa8/dafd463 pointers, refreshes the NEXT
  section to "track A spec DONE (#617); GAP-20 wiring is the next concrete action (a CPO pick — present,
  do not auto-start)", prepends #617 + #616 to RECENT PRs, and records the two wiring-PR advisories.
  Invents NO product/UX/metric/naming decision.

decisions_reserved:
  - Whether to proceed to the GAP-20 wiring PR next vs another track — a CPO pick (present candidates).
  - Whether folding a closed gap's spec-sync into its gap PR generalises — still open, CPO call.
  - The two stale-wireframe flags + the wireframe §10 doc-status sweep — separate items, not touched here.

done_when:
  - active_work.md header, "main carries" line, the FIRST-STEPS/NEXT section, RECENT PRs, and the
    track-A backlog entry are current (post-#617; spec done, GAP-20 wiring next with its two advisories);
    no other status claim changes.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
