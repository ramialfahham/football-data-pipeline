# Task contract — chore: refresh the handover after the idle-mode completeness fix

> Bookkeeping. Update .claude/active_work.md so a fresh session continues correctly: record this session's
> idle-mode fixtures-completeness fix (PR #514 carry-forward + the zero-API recovery + PR #515 the restored
> FK guard, all merged), the filed #517 (stale wrong-id purge) + #518 (process/behavioural retrospective),
> and re-point FIRST/NEXT (the deep-season backfill — the original NEXT #1 — is STILL pending; the recovery
> only restored what was already in RAW). Preserve all durable standing sections verbatim. No code.
> active_work.md is artifact-only for commits but NOT auto-editable, so it is in scope_paths; the commit
> also carries contract.md (never review-exempt) -> scope-auditor reviews.

objective: >
  Update the session-specific parts of .claude/active_work.md: the Last-updated line, FIRST, the
  This-session section (replace the prior TEAM-benchmark session with the 2026-06-19 idle-mode fix:
  root cause, #514 carry-forward, the zero-API recovery incl. the CNL/CDR/DFBP stale-id correction, #515
  the restored FK guard, #517/#518 filed, and the don't-re-litigate dbt ruling that fct_fixture stays
  full-refresh), and the NEXT pointer (the deep-season backfill is still pending; add #517/#518). Carry ALL
  durable standing sections (Standing authority, Product roadmap, the other NEXT items + Carryovers,
  dim_team, governance, form-window vocab, parked, pending CPO actions, Do-NOT, Environment) forward
  UNCHANGED + verbatim.

refs: >
  This conversation 2026-06-19. Merged #514 (idle-mode carry-forward) + #515 (fct_fixture FK guard); ran
  the zero-API recovery (25 leagues from RAW; CNL/CDR/DFBP stale-id corrected). Filed #517 + #518.
  Memory: [[feedback-raw-staging-latest-payload]], [[feedback-no-hacky-solutions]].

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed the handover refresh + the housekeeping this conversation ("do the proposed housekeeping",
  "create an issue"). Pure bookkeeping: records the already-merged #514/#515, the recovery, the filed
  #517/#518, and re-points NEXT. No new product / metric / naming / layer decision — the idle-fix design
  rulings (fct_fixture stays full-refresh; the carry-forward write-boundary fix) are already shipped and
  are recorded, not re-decided. Durable standing sections preserved verbatim.

decisions_reserved:
  - No new scope. NEXT items remain CPO-directed; this is not the place to add or re-decide them.
  - If anything beyond active_work.md needs editing, STOP — that is not bookkeeping.

done_when:
  - .claude/active_work.md reflects: #514 + #515 merged; the zero-API recovery + the CNL/CDR/DFBP stale-id
    correction; #517 + #518 filed; FIRST/NEXT re-pointed (deep-season backfill still pending — recovery only
    restored what was in RAW); the idle-fix session recorded; all durable sections intact + verbatim.
  - Commit on branch chore/handover-refresh-idle-fix; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
