# Task contract — end-of-day handover refresh (2026-06-28)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Artifact/handover task — `.claude/active_work.md` is NOT auto-editable, so it is named in scope_paths.

objective: >
  Rewrite `.claude/active_work.md` to current truth at end of the 2026-06-27/28 session: the macro-cleanup
  thread is COMPLETE — #590 (step-6 teardown cand. 1+4), #592 (macro standard), #593 (team_benchmark_metrics
  macro REMOVED via COMPOSE), #594 (standard trimmed) all merged. Record the locked decisions (player
  benchmark macro KEPT — it encodes B3 eligibility logic; seed-ify deferred to ship time; the "dead macro
  cluster" was a mirage), this session's hard-won lessons (COMPOSE de-macro recipe, macros-are-judgment, the
  standard-trim feedback, no local dbt validation at all this session), the updated #500 status + NEXT
  candidates, and keep the durable sections (governance machinery, form-window vocab, parked state, pending
  CPO actions, key specs, do-NOTs). State plainly that there is NO locked next task — the CPO directs.

refs: end-of-day handover; #590 + #592 + #593 + #594 merged; macro thread complete; player macro KEPT (B3); next is CPO-directed.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Documentation only — no product/code/§10 decision. Records what merged + the locked macro decisions and
  re-points the handover at the NEXT candidates (CPO-directed). No new decision is made here.

decisions_reserved:
  - None new. The next unit is CPO-directed; player-eligibility-seed is deferred to player-benchmark ship time.

done_when:
  - active_work.md leads with the macro thread COMPLETE (#590/#592/#593/#594 merged), nothing pending-merge,
    NO locked next task (CPO directs), the locked macro decisions, this session's lessons, the governance
    machinery + do-NOTs intact, and an accurate NEXT-candidates list.
  - Routes to scope-auditor only (active_work.md is in no routing path; the commit carries contract.md so it
    is NOT artifact-exempt — scope-auditor must run). CPO merges.

amendments: (none)
