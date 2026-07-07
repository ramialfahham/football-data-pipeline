# Task contract — handover refresh (session-boundary batch, post-#665)

> Written on a CLEAN tree (branch chore/handover-refresh-post-665 off main @ c1d9b2c).
> Bookkeeping only — batched session-boundary refresh ([[feedback-handover-discipline]]: refresh ONCE at the
> boundary). Plan mode skipped per the CPO carve-out; still runs the contract + review + gate.

objective: >
  Bring `.claude/active_work.md` current from post-#653 (pointer 712f16b) to post-#665 (c1d9b2c). Session arc:
  #661 (handover + metrics_context_model §8 de-stale), #662 (content_architecture board reconcile), #663
  (competition-header registry identity fields → competition hub), #664 (Team → Stats vs-league benchmark
  wireframe spec, screen 14), #665 (GAP-23 — wire mart_team_competition_benchmarks into the team payload). Record
  the ⭐ MILESTONE: after #665 the v2 data-foundation board has **NO orphans** — every built mart the frontend
  needs is wired (team benchmark spec #664 + wiring #665 was the last orphan). Remaining non-green rows are the
  TWO deliberate deferrals only: opponent-context (SHELVED) + coach (un-ingested) — both CPO policy calls.
  Compress the bloated lead. NEXT = an OPEN CPO pick; the natural big frontier is now the v2 FRONTEND (Phase E),
  unblocked by the green foundation (but still CPO-gated; live MVP untouched until cutover #377).
refs: #665 (GAP-23 wiring, c1d9b2c); #664 (screen 14 spec); #663 (competition header); #662 (board reconcile); #661 (handover + §8 de-stale).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  Doc/bookkeeping only. Single substantive file is `.claude/active_work.md`. No dbt_project/** model, no
  scripts/export_*.py, no ingestion/**, no site*/ change — no data/number/metric move, no build impact. The task
  scaffolding (.claude/task/**) is artifact-only; contract.md is artifact_only_never so this commit is NOT
  review-exempt (scope-auditor required).

decisions_taken: >
  Record-only. #661–#665 already merged (c1d9b2c). The "foundation has no orphans" milestone is a recorded finding,
  not a new decision. NEXT stays an OPEN CPO pick; the frontend (Phase E) is named as the natural next frontier but
  remains CPO-gated (not auto-started). No new roadmap invented.

decisions_reserved:
  - The actual next task (frontend Phase E; the 2 policy calls opponent-context/coach; matchday-schedule board
    note; task_f876b853 chip; the #545–#547 programs; #530(c)) — CPO picks later.

done_when:
  - active_work.md header + FIRST STEPS point at c1d9b2c; #665 recorded as the latest merged PR; the bloated lead compressed.
  - main-carries appends #661–#665; RECENT PRs prepends #663/#664/#665.
  - The ⭐ no-orphans / foundation-green milestone is recorded; NEXT names the frontend (Phase E) as the frontier
    (CPO-gated) + the small backlog; the 2 policy deferrals (opponent-context/coach) noted.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
