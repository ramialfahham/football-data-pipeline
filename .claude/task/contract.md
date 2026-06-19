# Task contract — chore: refresh the handover after Task A (#503 + #507 + #508 merged)

> Bookkeeping. Update .claude/active_work.md so a fresh session continues correctly: record this session's
> merges (mart_roster #503, the leaderboard composites #507, mart_leaderboards + full consolidation #508 —
> Task A COMPLETE), the issues filed (#504 metric_definitions cleanup, #505 docs audit, #506 deferred rate
> boards), the doc-clutter feedback, and re-point NEXT (Task A done → the remaining content-architecture
> items). Preserve all durable standing sections verbatim. No code. active_work.md is artifact-only for
> commits but NOT auto-editable, so it is in scope_paths. The commit also carries contract.md (never
> review-exempt) → scope-auditor reviews.

objective: >
  Update the session-specific parts of .claude/active_work.md: the Last-updated line (main 279dcff; #503 +
  #507 + #508 merged = Task A complete; #504/#505/#506 filed), FIRST (nothing pending; NEXT re-pointed), the
  This-session section (replace the 2026-06-18 metric-layer session with the 2026-06-19 Task A session + the
  doc-clutter lesson), NEXT #2 marked DONE, the #506 carryover, the retired-mart_player_season reference in
  Key specs corrected to mart_leaderboards, and the doc-clutter process lesson. Carry ALL durable sections
  (Standing authority, Product roadmap, the other NEXT items + Carryovers, dim_team, governance, form-window
  vocab, parked, pending CPO actions, Do-NOT, Environment) forward UNCHANGED + verbatim.

refs: >
  This conversation 2026-06-19. Merged #503 (mart_roster) + #507 (composites) + #508 (mart_leaderboards +
  consolidation); main 279dcff. Filed #504/#505/#506. Memory: [[project-leaderboards-roster-design]],
  [[feedback-doc-clutter-discipline]].

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed the handover refresh this conversation (2026-06-19, "yes, refresh"). Pure bookkeeping:
  records the already-merged Task A (#503/#507/#508), the filed issues (#504/#505/#506), and re-points NEXT.
  No new product / metric / naming / layer decision. Durable standing sections preserved verbatim.

decisions_reserved:
  - No new scope. The NEXT items (the remaining content-architecture sequence) are unchanged and remain
    CPO-directed; this is not the place to add or re-decide them.
  - If anything beyond active_work.md needs editing, STOP — that is not bookkeeping.

done_when:
  - .claude/active_work.md reflects: #503 + #507 + #508 merged (Task A complete; main 279dcff);
    #504/#505/#506 filed; FIRST = nothing pending + NEXT re-pointed; the Task A session + the doc-clutter
    lesson recorded; the retired mart_player_season reference in Key specs corrected to mart_leaderboards;
    all durable sections intact + verbatim.
  - Commit on branch chore/handover-refresh-task-a; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
