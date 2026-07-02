# Task contract — handover refresh (post-#634; GAP-22 merged, Career chain wired)

> Written on a CLEAN tree (branch chore/handover-refresh-634 off main @ 28999bc).
> Bookkeeping only — no code/model change. Records that #634 merged (GAP-22 — mart_player_career wired into
> the v2 player export + a club_latest_kickoff_at ordering column on the mart). Handover refreshes skip plan
> mode (CPO carve-out 2026-06-30).

objective: >
  #634 is MERGED (main @ 28999bc): GAP-22 — the per-club mart_player_career is now carried by the v2 player
  export as a top-level career[] block + national_appearances_total; ordering is a pure sort over two
  mart-shipped recency signals (last_kickoff_at + NEW club_latest_kickoff_at window column) so clubs are
  contiguous + newest-first. The Career chain is now WIRED end-to-end: model (#630) -> screen spec (#632) ->
  export (#634). Refresh active_work.md: NEXT = a CPO pick (the history backfill §10 cost / the doc-sync
  reconciliation chip task_4c709bd9 / Phase C continued / Phase D). Records merged facts only.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Header -> post-#634 / main @ 28999bc leading with GAP-22 wired; add #634 to the "main
  carries" line + prepend it to RECENT PRs; flip the Career mart line from "not wired" to WIRED (#634) across
  the gap map / Track A / Phase C; FIRST STEPS step 3 candidates updated (Career chain wired -> next = backfill
  / doc-sync reconciliation / Phase C / Phase D). Records the 4-round review saga briefly + the
  club_latest_kickoff_at ordering column. Invents nothing; locks no next task.

decisions_reserved:
  - The next task — CPO picks: the history backfill (§10 cost — gives Career/season-over-season real depth),
    the post-wiring doc-sync reconciliation (chip task_4c709bd9), Phase C continued (player YoY/streaks), or
    Phase D flagship marts. Present candidates; do NOT pre-decide.
  - The not_null hardening on last_kickoff_at / club_latest_kickoff_at (thrice-flagged, non-blocking) — a
    trivial future add; fold into the reconciliation or a mart touch.
  - All §10 unchanged.

done_when:
  - active_work.md: header post-#634 (main @ 28999bc); Career chain WIRED (#630/#632/#634) across the gap map;
    #634 in "main carries" + RECENT PRs; NEXT = CPO backlog pick; self-contained for a cold chat.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
