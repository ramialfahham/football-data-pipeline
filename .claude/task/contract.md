# Task contract — handover fix: drop untracked "further player-season models" candidates

> Written on a CLEAN tree (branch chore/handover-drop-untracked-candidates off main @ d5bacf4).
> Bookkeeping only — corrects `.claude/active_work.md`. Plan mode skipped per the CPO handover
> carve-out (2026-06-30); still runs the contract + review + gate.

objective: >
  Remove the brainstormed, UNTRACKED "further player-season models" candidates (multi-season trend /
  per-position YoY / milestones) from the handover. These were surfaced by this session's Explore-agent
  landscape brainstorm and offered as declined options in the "which YoY-extension" AskUserQuestion (the CPO
  picked "enrich existing YoY block", now shipped as #648); they were never a tracked or CPO-agreed roadmap.
  The prior refresh (#649) over-formalized them into the durable handover as "remaining candidates", which
  reads as a real queue. CPO direction (this session): DROP them entirely; keep only the genuinely tracked
  backlog (#530(b), #510, #484) as candidates. Fix all three occurrences (header NEXT clause, FIRST STEPS
  step 3, the Phase C backlog entry).

refs: corrects #649 (post-#648 refresh); CPO direction this session (AskUserQuestion — "Drop them entirely").

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  Doc/bookkeeping only. The single substantive file is `.claude/active_work.md`. No dbt_project/** model, no
  scripts/export_*.py, no ingestion/**, no site*/ change — no data/number/metric moves, no build impact. The
  task scaffolding (.claude/task/**) is artifact-only; contract.md is artifact_only_never so this commit is
  NOT review-exempt (scope-auditor required).

decisions_taken: >
  Record/correct-only. CPO ruled (this session) to DROP the untracked "further player-season models" ideas
  from the handover rather than relabel them. No new roadmap is created; the real tracked candidates
  (#530(b) player metric rows, #510 dribbles_success_pct retire, #484 player NT/tournament window) remain.
  NEXT stays an OPEN CPO pick.

decisions_reserved:
  - The actual next task (from the tracked backlog, or a fresh CPO-directed spec) — CPO picks later.

done_when:
  - The header NEXT clause, FIRST STEPS step 3, and the Phase C backlog entry no longer list
    trend/per-position/milestones as "candidates"; only #530(b)/#510/#484 remain as tracked candidates.
  - Pointer/main-GREEN and all other handover facts left intact and correct.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: []
