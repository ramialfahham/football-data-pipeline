# Task contract — handover refresh (post-#623; prep a fresh chat)

> Written on a CLEAN tree (branch chore/handover-refresh-623 off main @ 9ee17be).
> Bookkeeping only — no code/model/doc-of-record change. Final refresh before handing to a fresh chat:
> corrects the two wording/scope items the CPO resolved AFTER #623 locked. See docs/working_agreement.md §2.
> Handover refreshes skip plan mode.

objective: >
  #623 (handover refresh) is MERGED (main @ 9ee17be), but the CPO resolved two items AFTER it locked, so
  the merged handover is stale on them: (1) the median-band word is **"median"** (CONFIRMED), NOT the
  "provisionally 'middle', CPO-to-confirm" that #623 records; (2) the naked-% denominators item is
  RESOLVED (the denominator atoms exist in `int_player_season_position__metrics`, where the % is computed
  from them — e.g. duels_won/duels_total; carry num/den into the benchmark payload and show the triple — a
  shaping step, not an open CPO call), NOT the "OPEN, don't guess" #623 records. Make active_work.md accurate + fully self-contained so a fresh chat can
  resume the Player Stats wireframe rework with all four rework items settled/resolved.

refs: >
  main @ 9ee17be (#623). Parked: stash@{0} on docs/391-player-stats-percentile-spec ("wip: 12_player_stats").
  Display contract (now fully settled) in memory [[feedback-percentile-display-phrasing]]: ladder = top X% /
  median / bottom X%; ratio metrics show the {num} of {den} · {pct}% triple (carry the atoms).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. In the PARKED WIREFRAME callout: item 1 median word → "median" CONFIRMED (was
  provisional "middle"); item 4 naked-% → RESOLVED (carry the denominator atoms + show the triple; a
  shaping step, not an open call) — so all four rework items are now settled/resolved. Bump the header to
  post-#623 / all-wording-settled; set NEXT = resume the wireframe rework (recover the stash + apply). Add
  #623 to the "main carries" line + RECENT PRs. Records CPO decisions already made this session — invents
  nothing new.

decisions_reserved:
  - The wireframe rework itself — its own continuation (recover stash → rework → bi-analyst/scope-auditor).
  - Flagged follow-ups: the benchmark→player-export wiring PR (carries the squad[]-style block + the
    denominator atoms); season-model single-source repoint; remaining #530(b) rows (goals_penalty,
    goals_open_play metrics); Career screen; Phase C / Phase D.

done_when:
  - active_work.md: median word = "median" (settled), naked-% resolved, all 4 rework items settled/resolved,
    NEXT = resume the wireframe rework, #623 recorded; self-contained for a cold chat.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
