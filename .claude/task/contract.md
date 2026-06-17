# Task contract — chore: refresh the handover after #491 (player performance-surface spec)

> Bookkeeping task. Update `.claude/active_work.md` to record the merged player performance-surface
> spec (#491, merged → main 4a1a348) and reset NEXT to the build follow-ups (#480 / #484). No code,
> no docs-content change — handover only. `active_work.md` is artifact-only for commit purposes but
> not auto-editable, so it is added to scope_paths here (per the edit-gate scope rule). The commit
> also carries contract.md (this file) which is never review-exempt, so scope-auditor reviews.

objective: >
  Rewrite .claude/active_work.md so a fresh session continues correctly: record this session
  (player performance-surface spec merged as #491), set FIRST/NEXT to the build follow-ups, and
  carry forward the durable standing sections (authority, governance machinery, parked state,
  pending CPO actions, do-NOTs, environment notes) unchanged.

refs: >
  This conversation 2026-06-17. Player performance-surface spec PR #491 (merged, main 4a1a348),
  resolving docs/metrics_context_model.md §7 (player part) with a new §8. Build follow-ups #480 / #484.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed "update the handover" this conversation (2026-06-17). Pure bookkeeping: no product,
  metric, naming, or layer decision is made or changed here — it records decisions already merged in
  #491 and re-points NEXT. The durable standing sections are preserved verbatim.

decisions_reserved:
  - No new scope. The build PRs (#480 one canonical player-season model; #484 NT-context window) are
    CPO-directed and NOT started here. The display-contract amendment (appearance block +
    no-framing) to docs/wireframes/metrics_display.md stays a bi-analyst-owned follow-up.
  - If anything beyond active_work.md would need editing to "refresh the handover", STOP — that is no
    longer bookkeeping.

done_when:
  - .claude/active_work.md reflects: #491 merged (main 4a1a348); FIRST = nothing pending-merge;
    NEXT = #480 / #484 (+ the carried-over open items); durable sections intact.
  - Commit is the handover commit on branch chore/handover-player-spec; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
