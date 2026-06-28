# Task contract — refresh active_work.md handover (post-#596 formalization)

> Handover refresh. Written on a CLEAN tree (main @ 01bf81d). Doc-only — no code/model change.

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the CURRENT state: #596
  (metric_catalogue formula formalization) MERGED; the CPO formula-vs-availability ruling; the 4
  deferred rows + the follow-up queue; the SoT deserved-vs-actual thread (validated, NOT built); the
  governance machinery and standing rules. No code change.

refs: >
  This session arc: SoT deserved-vs-actual finding (sot_difference +0.70 vs league rank) → metric-layer
  scrutiny → metric_catalogue formula formalization ([#596] MERGED) + the CPO formula-vs-availability
  ruling. Mirrors prior handover refreshes (e.g. d279386 for #590).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS decisions already made (citing their source), invents none.
  The formula-vs-availability ruling is the CPO's in-session ruling, recorded in the MERGED #596
  contract `decisions_taken` + memory [[feedback-metric-formula-vs-availability]]. The SoT rank-space
  design is the CPO's in-session design lock, recorded in memory [[project-team-metric-rank-correlation-sweep]]
  (not yet built; catalogue rows still need CPO sign-off). The 4 deferred catalogue rows were
  CPO-approved follow-ups in #596 (its amendments). No NEW design / product / metric / naming /
  mechanism decision here.

decisions_reserved:
  - The next task (SoT build / PR2 resolvability check / split the 2 entity-dual rows / add player-leg
    goals_penalty / model-conformance) is the CPO's pick at the start of the next chat — the handover
    records state, it does not choose.

done_when:
  - active_work.md names #596 MERGED (catalogue formalization), main GREEN, the formula-vs-availability
    ruling, the 4 deferred rows + follow-ups, the SoT thread state, and the standing rules / Do-NOTs.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
