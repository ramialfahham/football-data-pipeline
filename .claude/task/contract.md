# Task contract — chore: refresh the handover after #493 (content architecture) + #494/#480 merged

> Bookkeeping. Update `.claude/active_work.md` to record the work merged since the last handover —
> #493 (content_architecture.md, the modular IA) and #494/#480 (player-season consolidation) — and
> re-point NEXT to the content-architecture build sequence. No code, no docs-content change.
> `active_work.md` is artifact-only for commits but not auto-editable, so it is in scope_paths here.
> The commit also carries contract.md (never review-exempt) → scope-auditor reviews.

objective: >
  Rewrite .claude/active_work.md so a fresh session continues correctly: record this session's merges
  (#491 spec, #493 content architecture, #494/#480 player-season consolidation), set FIRST/NEXT to the
  content_architecture.md build sequence (backfill → leaderboards/roster → benchmark → coaches/career)
  + the carryovers, and carry the durable standing sections forward unchanged.

refs: >
  This conversation 2026-06-17. Merged: #491 (player perf-surface spec §8), #492 (handover), #493
  (docs/content_architecture.md), #494/#480 (one canonical player-season model). main at 93a2957.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed the handover refresh this conversation (2026-06-17). Pure bookkeeping: records
  already-merged work + the CPO-locked design decisions (the content architecture, the flagship reads,
  the backfill depth policy) and re-points NEXT. No new product/metric/naming/layer decision is made.
  Durable standing sections preserved.

decisions_reserved:
  - No new scope. Every NEXT item (backfill, the new marts, coaches ingest, #484) is its own
    CPO-directed PR; the backfill EXECUTION (setting registry history_seasons + running it) is a
    cost-gated ingest task.
  - If anything beyond active_work.md needs editing to refresh the handover, STOP — not bookkeeping.

done_when:
  - .claude/active_work.md reflects: #491/#492/#493/#494 merged (main 93a2957); FIRST = nothing
    pending-merge; NEXT = the content_architecture build sequence + carryovers; the flagship decisions
    + backfill policy recorded; durable sections intact.
  - Commit on branch chore/handover-480-content-arch; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
