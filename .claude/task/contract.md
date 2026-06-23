# Task contract — session handover refresh (2026-06-23, benchmark PR2 close)

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the CURRENT state. This session built +
  merged #561 (player benchmark PR2 — the engine + mart + macro), with three build-time CPO refinements to
  the originally-locked design (B1 position source, B2 per-position floor/grain, B3 per-position metric
  eligibility). Record: the merge; those refinements; the re-pointed open queue (PR2 no longer "next"). No
  code; handover doc only.
refs: >
  CPO directed "Refresh handover & close" after merging #561. The PR2 build-time rulings are logged in
  `.claude/task/escalations.log` (2026-06-23 "player competition benchmark PR2" B1/B2/B3). Pattern: prior
  handover refreshes (e.g. the benchmark-PR1 close this morning).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: NONE — documentation/handover only. No dbt model, seed, script, registry, or CI change.
  downstream: the next chat's SessionStart hook reads .claude/active_work.md; no warehouse/build impact.
  layer_rules: n/a (no model touched). deploy_order: n/a — doc merge to main; nothing builds.
  blast_radius: NONE — handover text only; no shipped number moves.

decisions_taken: >
  Reflect already-merged facts only — no NEW design this refresh. #561 (PR2) is merged (main GREEN). The
  benchmark section is rewritten from "PR2 build-ready" to "PR2 MERGED" + the three B1/B2/B3 refinements
  (position_code source, 270-min-in-position floor + in-position value grain, per-position eligibility map,
  percent_rank percentile). The two-track operating model + program epics carry forward. Status + design-
  capture refresh, not a re-scope.

decisions_reserved:
  - What the next stretch builds (a program tranche, opponent-context v1.x, Coach/career marts, #500
    column-align, or wiring the benchmark into an export) is the CPO's pick at the start of the next chat —
    the handover records the merged state + the open queue, it does not choose.

done_when:
  - active_work.md status line names #561 (player benchmark PR2) MERGED, main GREEN, no open PRs.
  - The benchmark section records PR2 as MERGED with the B1/B2/B3 refinements (and the new models
    int_player_season_position__metrics / int_competition_benchmarks__player / mart_competition_benchmarks__player).
  - FIRST-next-session no longer says "build PR2"; the open queue is re-pointed.
  - Last-updated stamp moved to 2026-06-23 (benchmark-PR2 close).
  - check_task_artifacts passes; scope-auditor PASS; diff within scope_paths.

amendments: (none)
