# Task contract — handover refresh (post-#630; #480 §8.3 per-club foundation merged)

> Written on a CLEAN tree (branch chore/handover-refresh-630 off main @ 7bebac7).
> Bookkeeping only — no code/model change. Records that #630 merged (the #480 §8.3 per-club
> player-season foundation + rebuilt mart_player_career) and re-points the next chat at the updated
> backlog. Handover refreshes skip plan mode (CPO carve-out 2026-06-30). See docs/working_agreement.md §2.

objective: >
  #630 is MERGED (main @ 7bebac7): #480 §8.3 — NEW int_player_club_season__metrics (canonical per-club
  atoms base, grain player×club×competition-season); int_player_season__metrics re-expressed as a
  byte-identical composition of it (mart_player_profile + mart_leaderboards unchanged, CI-verified);
  mart_player_career rebuilt to the per-club × competition-season career log; int_player_career__metrics
  retired. This is Phase C brick 1. Refresh active_work.md so a fresh chat resumes cleanly: the Career
  surface is now DATA-unblocked (mart at the right grain, still orphan/unspec'd/thin-until-backfill);
  NEXT = a CPO pick (Career screen spec / Phase C continued / backfill / Phase D). Records merged facts only.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Header → post-#630 / main @ 7bebac7 leading with the #480 §8.3 foundation; add #630 to
  the "main carries" line + prepend it to RECENT PRs; FIRST STEPS step 3 + the backlog updated to reflect
  the per-club mart now built (career screen spec now against the rebuilt mart; wiring + backfill pending).
  Records the byte-stability property + the 4-round review. Invents nothing new; locks no next task.

decisions_reserved:
  - The next task — CPO picks: Career screen spec (13, against the rebuilt per-club mart), Phase C continued
    (player YoY/streaks on the new base), the history backfill (§10 cost), or Phase D flagship marts. Present
    candidates; do NOT pre-decide.
  - All §10 unchanged (product/UX, metrics, naming, new mechanisms, backfill depth/cost).

done_when:
  - active_work.md: header post-#630 (main @ 7bebac7); #480 §8.3 foundation recorded; mart_player_career
    now built-at-per-club-grain (orphan, unspec'd, thin-until-backfill); #630 in "main carries" + RECENT PRs;
    NEXT = CPO backlog pick; self-contained for a cold chat.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
