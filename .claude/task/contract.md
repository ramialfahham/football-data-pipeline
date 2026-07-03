# Task contract — handover refresh (post-#643; catch up #638 + #640–643)

> Written on a CLEAN tree (branch chore/handover-refresh-643 off main @ 87598cc).
> Bookkeeping only. main's active_work.md was STALE at post-#636 (the last landed refresh was #637); since
> then #638 (Phase C brick 1) + #640–643 (portfolio README + dbt-docs site) merged and NO handover landed
> (my post-#638 refresh #639 was superseded by #640–643 and CLOSED). Bring the handover current to post-#643.
> Handover refreshes skip plan mode (CPO carve-out 2026-06-30).

objective: >
  main @ 87598cc is SIX merges ahead of its handover (stuck at post-#636 / #637): #638 (Phase C brick 1 —
  player YoY int_player_profile__yoy -> mart_player_profile), and the portfolio arc #640 (README funnel +
  badges + architecture diagram) / #641 (MVP screenshot) / #642 (Design-decisions section) / #643 (public
  dbt docs lineage site at /dbt-docs/, folded into the existing Pages deploy). Also bank this session's
  BACKFILL FINDING (backfill effectively done — RAW + mart_player_career 5–10 seasons deep; "thin-until-backfill"
  was STALE). The post-#638 refresh #639 was superseded by #640–643 and CLOSED; this replaces it. NEXT =
  Phase C brick 2 (player streaks) / player season models / Phase D (a CPO pick). Records merged facts;
  locks no next task.
refs: #638; #640–#643; #391; #480; supersedes closed #639

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Header -> post-#643 / main @ 87598cc leading with Phase C brick 1 + the portfolio arc +
  the backfill finding; add #638 + #640–643 to the "main carries" line + prepend them to RECENT PRs; replace
  the "thin-until-backfill" framing with the finding (5–10 seasons deep); set NEXT = Phase C brick 2 / player
  season models / Phase D; keep the open follow-ups; note the CLOSED-#639 supersession. Invents nothing;
  locks no next task.

decisions_reserved:
  - The next task — CPO picks: Phase C brick 2 (player streaks, mirror int_team_profile__streaks), player
    season/YoY-extension models, or Phase D flagship marts (§10 method). Present candidates; do NOT pre-decide.
  - Portfolio remaining: the landscape social-preview image (a manual CPO step, per the #643 contract).
  - Two tiny doc follow-ups (metrics_display.md:91 stale GAP-21 ref; GAP-20 "id+name only").
  - Backfill marginal top-up (low value); not_null hardening on mart_player_career (non-blocking).
  - All §10 unchanged.

done_when:
  - active_work.md: header post-#643 (main @ 87598cc); #638 + #640–643 in "main carries" + RECENT PRs; the
    backfill finding banked; #639 supersession noted; NEXT = Phase C brick 2 / season / Phase D as a CPO pick;
    self-contained for a cold chat.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
