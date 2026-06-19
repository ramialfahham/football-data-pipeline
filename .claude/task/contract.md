# Task contract — chore: refresh the handover after the team competition benchmark (#511 + #512)

> Bookkeeping. Update .claude/active_work.md so a fresh session (the user is continuing in a new chat)
> continues correctly: record this session's merges (#511 metric direction/interpretation semantics,
> #512 mart_competition_benchmarks__team), the filed #510, the benchmark design + v1.x follow-ups, and
> re-point NEXT. Preserve all durable standing sections verbatim. No code. active_work.md is artifact-only
> for commits but NOT auto-editable, so it is in scope_paths; the commit also carries contract.md (never
> review-exempt) -> scope-auditor reviews.

objective: >
  Update the session-specific parts of .claude/active_work.md: the Last-updated line (main b8de817; #511 +
  #512 merged; #510 filed), FIRST (nothing pending; NEXT re-pointed), the This-session section (replace
  the Task-A session with the 2026-06-19 benchmark session — the direction/interpretation semantic, the
  team benchmark, the design rulings, the v1.x follow-ups), the NEXT items (#3 mart_competition_benchmarks
  DONE for teams; player + opponent-context = v1.x), and the open carryovers (#510 dribbles). Carry ALL
  durable sections (Standing authority, Product roadmap, the other NEXT items + Carryovers, dim_team,
  governance, form-window vocab, parked, pending CPO actions, Do-NOT, Environment) forward UNCHANGED +
  verbatim.

refs: >
  This conversation 2026-06-19. Merged #511 (metric direction/interpretation) + #512
  (mart_competition_benchmarks__team); main b8de817. Filed #510 (team dribbles retirement). Memory:
  [[project-competition-benchmarks-design]].

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed the handover refresh this conversation (2026-06-19, "continue in a new fresh chat soon").
  Pure bookkeeping: records the already-merged #511 + #512, the filed #510, the benchmark design + the
  v1.x follow-ups, and re-points NEXT. No new product / metric / naming / layer decision. Durable standing
  sections preserved verbatim.

decisions_reserved:
  - No new scope. The NEXT items remain CPO-directed; this is not the place to add or re-decide them.
  - If anything beyond active_work.md needs editing, STOP — that is not bookkeeping.

done_when:
  - .claude/active_work.md reflects: #511 + #512 merged (main b8de817); #510 filed; FIRST = nothing pending
    + NEXT re-pointed (team benchmark DONE; player benchmark + opponent-context = v1.x; backfill + coaches
    remain); the benchmark session + design recorded; all durable sections intact + verbatim.
  - Commit on branch chore/handover-refresh-benchmarks; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
