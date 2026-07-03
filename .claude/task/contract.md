# Task contract — handover refresh (post-#638; Phase C brick 1 merged)

> Written on a CLEAN tree (branch chore/handover-refresh-638 off main @ b38e00e).
> Bookkeeping only — no code/model change beyond the handover. Records that #638 merged (Phase C brick 1 —
> player year-over-year int_player_profile__yoy) AND banks this session's backfill finding (the backfill is
> effectively DONE — careers 5-10 seasons deep). Handover refreshes skip plan mode (CPO carve-out 2026-06-30).

objective: >
  #638 is MERGED (main @ b38e00e): Phase C brick 1 — NEW int_player_profile__yoy (the player mirror of the
  shipped team YoY int_team_profile__yoy) on int_player_season_record (per-club, appearance-aligned,
  domestic-only), with this-season-vs-last deltas for goals/assists/shots_on_goal/key_passes/defensive_actions
  (CPO metric set); composed into mart_player_profile via the primary club; auto-carries to the player export
  via select *. Also bank the SESSION FINDING: the history backfill is effectively DONE (RAW + mart_player_career
  are 5-10 seasons deep across domestic leagues; the "thin-until-backfill" premise was STALE) — so it is NOT
  the next task. Refresh active_work.md to post-#638: NEXT = Phase C continued (brick 2 player streaks / season
  models) or Phase D. Records merged facts + the finding; locks no next task.
refs: #638 (Phase C brick 1); #391; #480 §8

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Header -> post-#638 / main @ b38e00e leading with Phase C brick 1 + the backfill finding;
  add #638 to the "main carries" line + prepend it to RECENT PRs; **replace the "thin-until-backfill" /
  "history backfill" framing with the banked finding** (backfill effectively done — 5-10 seasons deep; the
  remaining gaps are marginal: VL/CNL at 2, some tournaments at 1 edition, a few continental at 5-9); set NEXT
  = Phase C brick 2 (player streaks, mirror int_team_profile__streaks) / player season models, or Phase D;
  keep the two tiny doc follow-ups (metrics_display.md:91; GAP-20 "id+name only"). Invents nothing; locks no next task.

decisions_reserved:
  - The next task — CPO picks: Phase C brick 2 (player streaks), player season/YoY-extension models, or
    Phase D flagship marts (opponent/schedule context + contribution-share, §10 method). Present candidates;
    do NOT pre-decide.
  - Backfill marginal top-up (VL/CNL to 5; EURO/COAM/AFCON/GCUP to 2 editions) — low value, a §10 cost call
    if ever wanted; some thinness is player-stats coverage a fixtures backfill won't fix. NOT decided.
  - Two tiny doc follow-ups (metrics_display.md:91 stale GAP-21 ref; GAP-20 "id+name only" loose note).
  - not_null hardening on mart_player_career.last_kickoff_at / club_latest_kickoff_at (non-blocking).
  - All §10 unchanged.

done_when:
  - active_work.md: header post-#638 (main @ b38e00e); #638 in "main carries" + RECENT PRs; the
    backfill-is-done finding banked (replacing thin-until-backfill framing); NEXT = Phase C brick 2 / season
    models / Phase D as a CPO pick; the follow-ups recorded; self-contained for a cold chat.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
