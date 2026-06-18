# Task contract — chore: refresh the handover after #497 (dbt MCP server) merged

> Bookkeeping. Update `.claude/active_work.md` so a fresh session continues correctly: record this
> session's merge (#497 — read-only dbt MCP server + the MCP-config PROTECTED classification), update
> FIRST + main SHA (dff05d7), note the server is live on restart, and preserve the content-architecture
> roadmap + all durable standing sections unchanged. No code, no docs-content change. active_work.md is
> artifact-only for commits but NOT auto-editable, so it is in scope_paths. The commit also carries
> contract.md (never review-exempt) → scope-auditor reviews.

objective: >
  Rewrite the session-specific parts of .claude/active_work.md to record the 2026-06-18 dbt MCP server
  work (#497 merged, main dff05d7), reframe the prior content-architecture merges as the roadmap basis for
  NEXT (unchanged), note the MCP server is live on session restart + its read-only tools, and add the
  MCP-config PROTECTED rule to the Do-NOT + Environment sections. Carry all durable standing sections
  (Standing authority, NEXT, Carryovers, key specs, dim_team, process lessons, governance, form-window
  vocab, parked, pending CPO actions, Do-NOT) forward unchanged.

refs: >
  This conversation 2026-06-18. Merged #497 (dbt MCP server + MCP-config protection), main dff05d7.
  See memory project-dbt-mcp-server.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed the handover refresh this conversation (2026-06-18, "Let's do it now"). Pure bookkeeping:
  records the already-merged #497 + the 2026-06-18 §10 ruling (MCP config PROTECTED) and re-points FIRST.
  No new product/metric/naming/layer decision. Durable standing sections preserved verbatim.

decisions_reserved:
  - No new scope. The NEXT items (the content-architecture build sequence) are unchanged + remain
    CPO-directed; this is not the place to add or re-decide them.
  - If anything beyond active_work.md needs editing to refresh the handover, STOP — not bookkeeping.

done_when:
  - .claude/active_work.md reflects: #497 merged (main dff05d7); FIRST = nothing pending-merge + the MCP
    server live on restart; the 2026-06-18 MCP session recorded; the content-architecture roadmap +
    flagship reads + backfill policy preserved as the NEXT basis; MCP-config PROTECTED rule in Do-NOT +
    Environment; all durable sections intact.
  - Commit on branch chore/handover-refresh-mcp; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
