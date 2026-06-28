# Task contract — refresh active_work.md handover (post-#598 SoT build merged)

> Handover refresh. Written on a CLEAN tree (main @ cc1bfd0). Doc-only — no code/model change.

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the CURRENT state: PR #598
  (TEAM deserved-vs-actual / SoT rank-space gap) MERGED to main; data-build GREEN; the 4 new
  metric_catalogue rows + the new int_team_season__deserved_vs_actual model live. Record the
  queued governance follow-up and the standing rules. No code change.

refs: >
  This session: built the TEAM deserved-vs-actual read (the flagship), catalogue-first, on the
  #596 formula-formalization foundation. PR #598 MERGED. Mirrors prior handover refreshes
  (#597 for #596, etc.).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS decisions already made (citing their source), invents
  none. The SoT build's design + the 4 catalogue rows + the §10 sub-calls are the CPO's in-session
  approvals, recorded in the MERGED #598 contract `decisions_taken` + memory
  [[project-team-metric-rank-correlation-sweep]]. The formula-vs-availability ruling is the
  standing CPO ruling [[feedback-metric-formula-vs-availability]]. No NEW design / product /
  metric / naming / mechanism decision here.

decisions_reserved:
  - The next task (the queued governance completeness test + #530 PR2 resolvability; or a fresh
    candidate) is the CPO's pick at the start of the next chat — the handover records state, it
    does not choose.

done_when:
  - active_work.md names #598 MERGED (TEAM deserved-vs-actual), main GREEN (data-build pass), the
    4 new catalogue rows + the new model, the queued governance follow-up, and the standing rules.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
