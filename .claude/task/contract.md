# Task contract — session handover refresh (2026-06-23, benchmark PR1 close)

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the CURRENT state. This session merged
  #558 (leaderboards rate boards → #506 CLOSED) + #559 (player per-90 metric layer = benchmark PR1).
  Record: those merges; the FULLY LOCKED player-benchmark PR2 design (so the next chat builds without
  re-litigating a long design); the leaderboards-vs-benchmark two-lens coherence ruling; the open queue.
  No code; handover doc only.
refs: >
  CPO directed wrapping the session for a fresh chat. The benchmark design was decided live by the CPO
  this session and is now logged durably in `.claude/task/escalations.log` (2026-06-23 "player
  competition benchmark — up-front CPO design rulings": per-90 + position-group peers + percentile/rank
  + floor 270 / finishing SoT>=10 + all-competitions + no prev-season fallback + the leaderboards-vs-
  benchmark two-lens ruling), per the 2026-06-17 E1 precedent. Pattern: prior handover refreshes.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: NONE — documentation/handover only. No dbt model, seed, script, registry, or CI change.
  downstream: the next chat's SessionStart hook reads .claude/active_work.md; no warehouse/build impact.
  layer_rules: n/a (no model touched). deploy_order: n/a — doc merge to main; nothing builds.
  blast_radius: NONE — handover text only; no shipped number moves.

decisions_taken: >
  Reflect already-merged facts + the CPO-locked benchmark design only — no NEW design this refresh.
  #558 + #559 are merged (main GREEN). The PR2 design block is the set of CPO rulings made live this
  session, recorded verbatim so the next chat does not re-decide. The two-track operating model + the
  program epics carry forward. This is a status + design-capture refresh, not a re-scope.

decisions_reserved:
  - What the next stretch builds (player benchmark PR2 vs a program tranche vs another product slice) is
    the CPO's pick at the start of the fresh chat — the handover records the locked PR2 design + the
    open queue, it does not choose.

done_when:
  - active_work.md status line names #558 + #559 (benchmark PR1) MERGED, main GREEN.
  - The locked player-benchmark PR2 design is recorded (engine + mart + macro + metric set + floor/
    peers/percentile/scope/no-fallback) + the leaderboards-vs-benchmark coherence ruling.
  - FIRST-next-session leads with PR2 (build-ready) + carries the open queue.
  - Last-updated stamp moved to 2026-06-23 (benchmark-PR1 close).
  - check_task_artifacts passes; scope-auditor PASS; diff within scope_paths.

amendments: (none)
