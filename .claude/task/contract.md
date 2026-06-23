# Task contract — session handover refresh (2026-06-23, deserved-vs-actual redesign queued)

objective: >
  Refresh .claude/active_work.md so the next chat continues from the CURRENT state. After the benchmark-PR2
  close, this session also: merged #563 (REMOVED the unapproved, uncatalogued performance_vs_results_gap
  metric from mart_team_profile), and queued the deserved-vs-actual REDESIGN as the next discussion. Record:
  the #563 removal; the deserved-vs-actual redesign as the next session's DESIGN discussion — TEAM ONLY (the
  CPO explicitly excluded players for now) — with the framing we developed (so it is not re-derived); and the
  #530 catalogue-first-enforcement governance gap surfaced this session. No code; handover doc only.
refs: >
  CPO directive: "do the refresh. we'll discuss deserved vs actual for teams (not players) tomorrow in a new
  chat." The #563 removal landed this session (the catalogue-governance violation from #324). Pattern: prior
  handover refreshes.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: NONE — documentation/handover only. No dbt model, seed, script, registry, or CI change.
  downstream: the next chat's SessionStart hook reads .claude/active_work.md; no warehouse/build impact.
  layer_rules: n/a. deploy_order: n/a — doc merge to main; nothing builds.
  blast_radius: NONE — handover text only; no shipped number moves.

decisions_taken: >
  Reflect merged facts + the CPO's directive only — NO new design decided. #563 merged (performance_vs_
  results_gap removed; shot_share_season + points_capture_season retained as catalogued metrics). The next
  session's first topic is the TEAM deserved-vs-actual redesign (a DESIGN discussion, NOT a build) — players
  are explicitly OUT of this round per the CPO. The framing developed this session is captured so it is not
  re-derived (the old metric's failure = comparability of non-commensurable shares; the candidate fix =
  percentile-space gap via the benchmark engine; no xG; catalogue-first; football-analytics owns the
  definition). The deserved-vs-actual METHOD + input set remain RESERVED for that discussion.

decisions_reserved:
  - The deserved-vs-actual definition (comparability method — percentile-space vs deserved-goals composite —
    the "deserved" input set, the "actual" set) is the TEAM design discussion tomorrow; football-analytics-
    owned §10. The handover records the framing + candidates, it does NOT decide.
  - Whether/when to prioritise #530 (CI-enforce catalogue-first traceability — the gap that let the #324
    metric slip) is the CPO's call.

done_when:
  - active_work.md status line names #563 (performance_vs_results_gap REMOVED) merged, main GREEN, no open PRs.
  - A deserved-vs-actual-redesign section captures: TEAM-only scope (players excluded this round), the
    comparability framing + the percentile-space candidate, no-xG, catalogue-first, football-analytics-owned.
  - FIRST-next-session LEADS with "discuss the TEAM deserved-vs-actual redesign (DESIGN, not build)".
  - #530 (catalogue-first enforcement gap) noted as the systemic governance follow-up.
  - Last-updated stamp moved to 2026-06-23 (deserved-redesign queued).
  - check_task_artifacts passes; scope-auditor PASS; diff within scope_paths.

amendments: (none)
