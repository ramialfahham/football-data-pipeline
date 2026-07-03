# Task contract — handover refresh (post-#636; doc-sync reconciliation merged)

> Written on a CLEAN tree (branch chore/handover-refresh-636 off main @ baef982).
> Bookkeeping only — no code/model/doc-content change beyond the handover itself. Records that #636 merged
> (post-wiring doc-sync reconciliation: wireframes 11/12/13 + the gaps register + content_architecture flipped
> to wired/shipped, and 12/13 §5 keys reconciled to the shipped export). Handover refreshes skip plan mode
> (CPO carve-out 2026-06-30) — show the diff inline, quick go, same contract+review+gate.

objective: >
  #636 is MERGED (main @ baef982): the 3 now-wired screens (Squad #619 / Stats-percentile #627 / Career #634)
  flipped proposed/pending/orphan -> wired/shipped across wireframes 11/12/13 + the gaps register (GAP-21/22)
  + content_architecture; per a CPO "full reconciliation" ruling (escalations.log 2026-07-02), 12/13's §5 JSON
  keys were also corrected to the shipped export payload. Refresh active_work.md to post-#636: NEXT = a CPO
  pick (history backfill §10 cost / Phase C continued / Phase D) — the doc-sync candidate is now DONE. Records
  merged facts + the two small open follow-ups; locks no next task.
refs: #636 (chip task_4c709bd9); #391

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Header -> post-#636 / main @ baef982, leading with the doc-sync reconciliation; add #636
  to the "main carries" line + prepend it to RECENT PRs; DROP the now-DONE doc-sync candidate from the NEXT
  list (leaving history backfill / Phase C / Phase D); flip the wireframes/register/content_architecture
  status language from "reconcile separately" to reconciled/done; record the two small open follow-ups
  (metrics_display.md:91 stale GAP-21 ref; GAP-20 "id+name only" loose note). Invents nothing; locks no next task.

decisions_reserved:
  - The next task — CPO picks: the history backfill (§10 cost — gives Career/season-over-season real depth),
    Phase C continued (player YoY/streaks on int_player_club_season__metrics), or Phase D flagship marts.
    Present candidates; do NOT pre-decide.
  - Two small open follow-ups (doc-only, surfaced by #636): metrics_display.md:91 still calls GAP-21 a future
    "wiring PR" (now shipped #627); GAP-20's register note "id+name only" is loose (shipped squad[] carries
    six identity fields). Each a tiny future doc touch; NOT decided here.
  - not_null hardening on mart_player_career.last_kickoff_at / club_latest_kickoff_at (thrice-flagged,
    non-blocking, transitively guaranteed) — a dbt model/yml change; still a future add.
  - All §10 unchanged.

done_when:
  - active_work.md: header post-#636 (main @ baef982); #636 in "main carries" + RECENT PRs; the doc-sync
    candidate dropped from NEXT (history backfill / Phase C / Phase D remain); the two follow-ups recorded;
    self-contained for a cold chat.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
