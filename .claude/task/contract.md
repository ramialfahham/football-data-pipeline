# Task contract — handover refresh (post-#625; Stats-percentile wireframe merged)

> Written on a CLEAN tree (branch chore/handover-refresh-625 off main @ ebbcfd4).
> Bookkeeping only — no code/model/doc-of-record change. Records that #625 merged (the reworked Player Stats
> percentile wireframe + GAP-21) and points the next chat at the wiring PR / backlog. Handover refreshes skip
> plan mode (CPO carve-out 2026-06-30). See docs/working_agreement.md §2.

objective: >
  #625 is MERGED (main @ ebbcfd4): the parked Player Stats percentile wireframe (docs/wireframes/12_player_stats.md)
  was recovered + reworked (median word = "median"; distributional-position framing honest for the 7 neutral
  metrics; all 18 metrics bound to real mart columns; ratio triple; two-line 03 footer) and GAP-21 (the
  benchmark->player-export wiring) registered. Refresh active_work.md so a fresh chat resumes cleanly: the
  Stats-percentile SCREEN is now SPEC'D (not just drafted/parked); NEXT = the GAP-21 wiring PR (the "cheap
  green") or a CPO pick from the backlog. Records merged facts only.

refs: >
  main @ ebbcfd4 (#625). Display contract banked in memory [[feedback-percentile-display-phrasing]] (updated
  this session with the distributional-position refinement + the rank-mirror detail). GAP-21 = wire
  mart_player_competition_benchmarks into shape_player_payload (carry the 5 ratio metrics num/den atoms).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Update the header to post-#625 / main @ ebbcfd4. Replace the "PARKED WIREFRAME — recover
  this first" callout (the wireframe is now merged) with a short "Stats-percentile SPEC'D (#625)" state +
  NEXT = GAP-21 wiring. Flip the benchmarks orphan-mart line drafted/parked -> SPEC'D (wiring still pending
  GAP-21). Add #625 to the "main carries" line + prepend it to RECENT PRs. Set FIRST STEPS step 3 to the
  wiring PR / backlog pick. Invents nothing new; records merged facts + the CPO-settled display framing.

decisions_reserved:
  - The next task itself — CPO picks: the GAP-21 benchmark->player-export wiring PR (analytics-engineer + cto
    + pytest tests/test_export_site_data.py) is the natural cheap green; else Career screen, Phase C (#480),
    Phase D. Present candidates; do NOT pre-decide.
  - All §10 (product/UX, metrics, naming, NEW mechanisms) — unchanged.

done_when:
  - active_work.md: header post-#625 (main @ ebbcfd4); parked-wireframe callout replaced with the SPEC'D
    state + NEXT = GAP-21 wiring; benchmarks orphan line -> SPEC'D; #625 in "main carries" + RECENT PRs;
    self-contained for a cold chat.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
