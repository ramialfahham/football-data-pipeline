# Task contract — handover refresh (post-#632; Career screen spec'd + GAP-22)

> Written on a CLEAN tree (branch chore/handover-refresh-632 off main @ 1132baa).
> Bookkeeping only — no code/model change. Records that #632 merged (the Player Career wireframe 13 +
> GAP-22) and re-points the next chat. Handover refreshes skip plan mode (CPO carve-out 2026-06-30).

objective: >
  #632 is MERGED (main @ 1132baa): docs/wireframes/13_player_career.md — the Player → Career sub-screen,
  field-bound to the per-club mart_player_career (#630); club-grouped season-by-season career log + national
  caps section, counts-only; GAP-22 registered (export wiring, pending); companion doc-syncs (00/99/03).
  Refresh active_work.md: the Career screen is now SPEC'D (was un-spec'd) — remaining Career work = GAP-22
  export wiring + the history backfill. NEXT = a CPO pick. Records merged facts only.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Header → post-#632 / main @ 1132baa leading with the Career spec; add #631 + #632 to the
  "main carries" line + prepend #632 to RECENT PRs; flip the gap map / Track A Career line from "un-spec'd"
  to "SPEC'D (#632); wiring = GAP-22 (pending)"; FIRST STEPS step 3 candidates updated (Career spec DONE →
  remaining = GAP-22 wiring + backfill; plus Phase C continued / Phase D). Invents nothing; locks no next task.

decisions_reserved:
  - The next task — CPO picks: GAP-22 (mart_player_career export wiring, incl. the subtotal precompute-vs-display
    call), the history backfill (§10 cost), Phase C continued (player YoY/streaks on the new base), or Phase D
    flagship marts. Present candidates; do NOT pre-decide.
  - All §10 unchanged.

done_when:
  - active_work.md: header post-#632 (main @ 1132baa); Career screen SPEC'D (#632) + GAP-22 pending across the
    gap map / Track A; #631 + #632 in "main carries"; #632 in RECENT PRs; NEXT = CPO backlog pick;
    self-contained for a cold chat.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
