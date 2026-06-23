# Task contract — session handover refresh (2026-06-23)

objective: >
  Refresh `.claude/active_work.md` so a fresh chat (handed this file by the SessionStart
  `handover_in` hook) continues from the CURRENT state. The on-main handover is the #526-closeout
  version and predates THREE merged PRs this session — it would start the next chat with a stale
  picture. Update the status line + the FIRST-next-session list to reflect: #500 (team-season
  consolidation) MERGED, mart_player_career (#555) MERGED, dim_coach + dim_coach_team_mapping (#556)
  MERGED. Re-point the product roadmap "next" (career + coaches are now DONE; the next product slices
  are the Coach/career CONSUMPTION marts — website #391 PAUSED — plus the deferred #500 column-alignment
  follow-up, #506 rate boards, player benchmark/opponent-context v1.x). No code; handover doc only.

refs: >
  CPO this session set the build order (career mart first, then coaches) — both shipped. User is moving
  to a fresh chat; the handover is the bridge. Two-track operating model (PRODUCT primary + PROGRAMS
  #545/#546/#547) unchanged. Pattern: prior handover refreshes (#542, #552, ea26884).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: NONE — documentation/handover only. No dbt model, seed, script, registry, or CI change.
  downstream: the next chat's SessionStart hook reads .claude/active_work.md; no warehouse/build impact.
  layer_rules: n/a (no model touched). check_layer_contract / registry-sync unaffected.
  deploy_order: n/a — doc merge to main; nothing builds.
  blast_radius: NONE — handover text only; no shipped number moves.

decisions_taken: >
  Reflect already-merged facts only — no NEW design or product call. #500 / #555 / #556 are merged
  (main GREEN). Career + coaches builds are DONE; their consumption marts stay DEFERRED (website #391
  PAUSED) per the standing CPO ruling, not re-decided here. The two-track model + program epics carry
  forward verbatim. This is a status refresh, not a re-scope.

decisions_reserved:
  - What the next stretch builds (next product slice vs a program tranche) is the CPO's pick at the
    start of the fresh chat — the handover LISTS the open queue, it does not choose.
  - #545 coverage tranche cut, #549/#550 governance designs, the #500 `_season`/goals_saves column
    alignment, #506 rate boards — all remain open CPO decisions, carried in the handover unchanged.

done_when:
  - active_work.md status line names #500 + mart_player_career (#555) + dim_coach/#556 as MERGED, main GREEN.
  - FIRST-next-session reflects career + coaches DONE; lists the open queue without choosing.
  - Last-updated stamp moved to 2026-06-23 (session-close refresh).
  - check_task_artifacts passes; scope-auditor PASS; diff within scope_paths.

amendments: (none)
