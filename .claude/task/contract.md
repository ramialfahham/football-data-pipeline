# Task contract — chore: refresh the handover after #499 + #501 merged

> Bookkeeping. Update `.claude/active_work.md` so a fresh session continues correctly: record this session's
> merges (#499 rating removal, #501 metric layer Phase 1), the metric-layer outcome + the over-build lesson,
> the new follow-up #500, and re-point NEXT to task A (leaderboards + roster). Preserve all durable standing
> sections verbatim. No code, no docs-content change. active_work.md is artifact-only for commits but NOT
> auto-editable, so it is in scope_paths. The commit also carries contract.md (never review-exempt) →
> scope-auditor reviews.

objective: >
  Update the session-specific parts of .claude/active_work.md: the Last-updated line (main 4353e41; #499 +
  #501 merged; #500 opened), FIRST (nothing pending; NEXT = task A on the metric-layer foundation; dbt MCP
  cold-start note), the This-session section (replace the MCP-server session with metric-layer Phase 1 + the
  rating-removal precursor + the over-build lesson), the team-consolidation carryover (now #500), and add the
  size-the-solution process lesson. Carry ALL durable sections (Standing authority, Product roadmap, NEXT,
  other Carryovers, Key specs, dim_team, governance, form-window vocab, parked, pending CPO actions, Do-NOT,
  Environment) forward UNCHANGED + verbatim.

refs: >
  This conversation 2026-06-18. Merged #499 (rating removal) + #501 (metric layer Phase 1), main 4353e41.
  Opened #500 (team-season naming + consolidation). Memory: [[feedback-no-hacky-solutions]],
  [[project-season-model-naming-parked]].

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed the handover refresh this conversation (2026-06-18, "do it"). Pure bookkeeping: records the
  already-merged #499 + #501, the metric-layer outcome (model + catalogue + drift test, NOT an engine) + the
  reverted over-build lesson, the new #500, and re-points NEXT to task A. No new product / metric / naming /
  layer decision. Durable standing sections preserved verbatim.

decisions_reserved:
  - No new scope. The NEXT items (task A + the content-architecture sequence) are unchanged and remain
    CPO-directed; this is not the place to add or re-decide them.
  - If anything beyond active_work.md needs editing, STOP — that is not bookkeeping.

done_when:
  - .claude/active_work.md reflects: #499 + #501 merged (main 4353e41); #500 opened; FIRST = nothing pending +
    NEXT = task A; the metric-layer Phase 1 session + the over-build lesson recorded; all durable sections
    intact and verbatim.
  - Commit on branch chore/handover-refresh-metric-layer; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
