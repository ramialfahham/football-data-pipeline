# Task contract — Handover refresh (2026-06-22 close-out: #518 impact-map gate)

objective: >
  Refresh .claude/active_work.md to the true post-merge state. This session shipped the #518
  impact-map gate as PR #540 (MERGED): the task contract now requires an EVIDENCED impact_map
  for any structural-surface edit (ingestion/**, dbt_project/models/**, scripts/export_*.py,
  site*/); task_contract_gate.py presence-gates it at the edit boundary; the three reviewer
  specs hunt it; working_agreement.md §2 + Appendix A6 document it. The bundled merge-on-write
  layering.md codification was de-scoped to #539 mid-review (RAW_APIF_FIXTURE_DETAILS is
  delete-on-retry-only, not the per-key upsert of RAW_APIF_PLAYERS). Update FIRST-next-session
  (drop the now-done "#518 tackle soon" item; surface #539); main green.

refs: >
  This conversation 2026-06-22. PR #540 (merged), issue #539 (layering follow-up). #518 closed
  by #540's mechanism. Memory: feedback-no-hacky-solutions (mode 5 = end-to-end-map-first).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation-only handover refresh — no code, no product decision. The commit carries
  contract.md (hashed, not artifact-exempt), so it needs review; routing for active_work.md +
  .claude/task/** is scope-auditor only. active_work.md is hash-excluded (artifact). No code
  paths touched.

decisions_reserved:
  - none. Pure handover bookkeeping.

done_when:
  - active_work.md reflects: #540 merged (impact-map gate live; what it gates + how);
    #539 filed (layering merge-on-write follow-up + why de-scoped); the "#518 tackle soon"
    item removed from FIRST-next-session; main green; FIRST next action set.
  - Tree matches the contract (only active_work.md + .claude/task/**).

amendments: (none)
