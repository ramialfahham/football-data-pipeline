# Task contract — record the Top teams ruling (one team per league)

objective: >
  Record today's CPO ruling on the Top teams home-page block: one team per pool league, same
  shape as Top players (2026-08-18). Update the wireframe's Open/Scope/display-rules sections,
  propose the replacement intro copy (mirroring the Top players copy pattern), and flag that
  (unlike the players mock) the Top teams mock does not already reflect this shape. Bookkeeping
  + a copy proposal, no code, no mart build.
refs: docs/wireframes/10_home.md §0 (Top players ruling, same date, same shape); GAP-29
  (team leaderboard mart, design approved, build not started — unaffected by this, still not
  started).

scope_paths:
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md
  - .claude/active_work.md
  - CLAUDE.md
  - .claude/task/escalations.log

decisions_taken: >
  CPO, this session: "one team per league, same as players" — the pooling-shape question for
  Top teams, mirroring the 2026-08-18 Top players ruling ("One per league -> yes, it's not a
  leaderboard in the defined pool.", recorded in 10_home.md's Closed-since-2026-08-04 list and
  GAP-31's withdrawal). CPO, same message: the mock's "Ranked across pooled leagues" intro line
  is confirmed incorrect for Top teams too and needs the same adjustment made for Top players'
  intro copy.

decisions_reserved:
  - The exact proposed Top teams intro copy string is DRAFTED here (mirroring the approved
    Top players line) but not yet CPO-approved — copy is always his, per docs/working_agreement.md
    DO NOT list. Marked PROPOSED, not APPROVED, in both edited files; escalated in chat this turn.

impact_map: >
  leaf/cosmetic: two wireframe-doc sections + the handover, no code, no model, no mart, no
  export, no site_v2 file. Nothing downstream reads these docs at build time. blast_radius: none.

done_when:
  - docs/wireframes/10_home.md's Open section carries a Top teams ruling entry mirroring the
    Top players one, including the mock-is-not-already-correct caveat.
  - The Scope paragraph's ⚠ note is broadened to cover both blocks, not players only.
  - A proposed (not approved) Top teams intro copy is recorded, parallel in structure to the
    approved Top players line.
  - .claude/active_work.md reflects the ruling and the still-open items (copy confirmation,
    mock rework, GAP-29 mart still not started), and is back under the 16,000-character cap.
  - Committed on this branch; MR opened by the post-commit hook.

amendments:
  - 2026-08-18: + `CLAUDE.md` — authority: the handover's own char cap + "delete one stale
    section, don't shave clauses" rule. Getting active_work.md back under cap means deleting the
    ⭐ PRIOR SESSION — #62 section whole. Two of its four traps are duplicated elsewhere (fnmatch/
    `[lang]` already in CLAUDE.md; the 680px/single-select/inert-rows decisions already in
    `08_browse.md`) and are safe to drop. Two are NOT duplicated anywhere (`world_championship`
    rename trap; a global-hook-conflict note) — relocating those into CLAUDE.md's own
    "Operational notes" section is the same move that section's own header already prescribes
    ("do not copy back: that file is not capped"), not new scope.
  - 2026-08-18: + `.claude/task/escalations.log` — authority: scope-auditor round-1 FAIL. The
    ruling this task records had no logged entry, unlike the sibling Top players ruling it
    mirrors (which does). Adding an entry, matching that entry's format, and declaring the path
    in scope so a reviewer can verify it independently of the contract's own narrative, per
    `docs/working_agreement.md`'s own statement that escalations are appended there.
