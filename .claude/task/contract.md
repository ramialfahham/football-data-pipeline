# Task contract — refresh active_work.md handover (post-#600 integrity tests merged)

> Handover refresh. Written on a CLEAN tree (main @ bc94b61). Doc-only — no code/model change.

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the CURRENT state: PR #600
  (metric_catalogue integrity guards — meaning completeness + #530 PR2 resolvability) MERGED to
  main; data-build GREEN; the 3 team open-play atoms now carry direction+interpretation. Record
  the remaining #530 follow-ups, the standing rules, and the session lessons (the BigQuery
  FROM-less-WHERE singular-test gotcha + the reset --soft commit collapse). No code change.

refs: >
  This session shipped 3 PRs: #598 (TEAM deserved-vs-actual / SoT rank-space gap), #599 (handover
  refresh), #600 (metric_catalogue integrity guards). Mirrors prior handover refreshes (#599, #597).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS decisions already made (citing their source), invents
  none. The #600 design (fill the 3 team atoms = higher_better + the completeness-test team-only /
  player-exempt scope + the resolvability stoplist) are the CPO's in-session approvals, recorded in
  the MERGED #600 contract `decisions_taken` + review.md escalations. No NEW design / product /
  metric / naming / mechanism decision here.

decisions_reserved:
  - The next task (the remaining #530 follow-ups, or a fresh candidate) is the CPO's pick at the
    start of the next chat — the handover records state, it does not choose.

done_when:
  - active_work.md names #600 MERGED (integrity guards), main GREEN, the 3 filled atoms, the
    remaining #530 follow-ups, the standing rules, and the new session lessons.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
