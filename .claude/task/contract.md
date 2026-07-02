# Task contract — handover refresh (post-#627; GAP-21 merged, Stats-percentile track CLOSED)

> Written on a CLEAN tree (branch chore/handover-refresh-627 off main @ 29e6190).
> Bookkeeping only — no code/model/doc-of-record change. Records that #627 merged (mart_player_competition_
> benchmarks wired into the player export) and points the next chat at the un-picked backlog. Handover
> refreshes skip plan mode (CPO carve-out 2026-06-30). See docs/working_agreement.md §2.

objective: >
  #627 is MERGED (main @ 29e6190): GAP-21 wired mart_player_competition_benchmarks into the v2 player export
  (per-season benchmarks[] block; the mart gained metric_numerator/metric_denominator for the ratio triple;
  int_player_season_position__metrics exposes goals_penalty). The Stats-percentile track is now CLOSED — the
  mart is built AND wired. Refresh active_work.md so a fresh chat resumes cleanly: next = the un-picked
  backlog (Career screen / Phase C #480 / Phase D), a CPO pick. Records merged facts only.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Header → post-#627 / main @ 29e6190; flip the Stats-percentile ⭐ callout from
  "SPEC'D, wiring next" to "CLOSED — mart built AND wired (#627)"; benchmarks orphan line → WIRED (✓); add
  #626 + #627 to the "main carries" line + prepend them to RECENT PRs; FIRST STEPS step 3 → CPO pick from the
  backlog. Records the two CI fixes in #627 (SQLFluff LT02; goals_penalty exposure via a CI-driven scope
  amendment). Invents nothing new.

decisions_reserved:
  - The next task — CPO picks: Career screen spec, Phase C (player-season #480), Phase D flagship marts, or
    the wireframe §10 doc-status sweep. Present candidates; do NOT pre-decide.
  - All §10 unchanged.

done_when:
  - active_work.md: header post-#627 (main @ 29e6190); Stats-percentile track CLOSED (built + wired);
    benchmarks orphan → WIRED; #626 + #627 in "main carries" + RECENT PRs; NEXT = CPO backlog pick;
    self-contained for a cold chat.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
