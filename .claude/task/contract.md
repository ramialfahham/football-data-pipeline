# Task contract — handover refresh (session-boundary batch, post-#651)

> Written on a CLEAN tree (branch chore/handover-refresh-post-651 off main @ cf36c19).
> Bookkeeping only — the batched session-boundary refresh ([[feedback-handover-discipline]] cadence rule:
> refresh ONCE at the boundary, not per-merge). Plan mode skipped per the CPO handover carve-out; still runs
> the contract + review + gate.

objective: >
  Bring `.claude/active_work.md` current from post-#648 (pointer 1966d4d) to post-#651 (cf36c19), folding in the
  session's net: #649 (post-#648 refresh), #650 (handover — drop untracked "further player-season models"),
  #651 (#530(b) — player goals_penalty + goals_open_play catalogue rows completed). Record the ⭐ premise-check
  finding that #510 (retire leftover team dribbles_success_pct) is ALREADY DONE (traced end-to-end: no team
  dribbles catalogue row / momentum-model refs / range test; export dribbles is player-only; issue CLOSED) — do
  NOT re-attempt; drop it from the carryovers. Note the spawned follow-up chip (task_f876b853: 2 stale "deferred"
  doc comments). NEXT tracked candidate narrows to #484 (player NT/tournament window).

refs: #651 (cf36c19 #530(b)); #650 (drop untracked candidates); #649 (post-#648 refresh); #510 (verified already-done, CLOSED).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  Doc/bookkeeping only. The single substantive file is `.claude/active_work.md`. No dbt_project/** model, no
  scripts/export_*.py, no ingestion/**, no site*/ change — no data/number/metric moves, no build impact. The
  task scaffolding (.claude/task/**) is artifact-only; contract.md is artifact_only_never so this commit is NOT
  review-exempt (scope-auditor required).

decisions_taken: >
  Record-only. #649/#650/#651 already merged (cf36c19). #510 recorded as already-done from a code-traced
  premise check (not a new decision — a finding). NEXT stays an OPEN CPO pick; the only remaining tracked
  candidate is #484. No new roadmap invented.

decisions_reserved:
  - The actual next task (#484, or a fresh CPO-directed spec) — CPO picks later.

done_when:
  - active_work.md header + FIRST STEPS point at cf36c19; #651 recorded as the latest merged PR.
  - main-carries appends #649 + #650 + #651; a #651 entry is prepended to RECENT PRs.
  - #530 follow-up (b) marked DONE #651; #510 recorded already-done and dropped from the carryovers; #484 is the remaining tracked candidate.
  - The spawned doc-nit chip (task_f876b853) is noted.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: []
