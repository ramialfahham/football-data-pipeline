# Review — chore/refresh-handover-611 — 2026-06-30

> G3 Lock artifact. Doc-only handover refresh: record #391 GAP-16 merged (#611); Phase B now has only
> GAP-01 left on the spec'd screens; next = CPO pick. Required set (routing): always → scope-auditor only
> — the diff touches `.claude/active_work.md` (artifact_only, hash-excluded) + `.claude/task/contract.md`
> (artifact_only_never → hashed, review required). No code path.

diff_sha256: 2d8d0b79daaab4625f5d1873ffc4fd40a089a99adabdbd3c5b9b440acb0f574d

## scope-auditor
VERDICT: PASS
risks_checked:
- Backlog-state accuracy + GAP-01 "pending": active_work.md is the single cold-chat state machine, so a wrong status ripples to every future session. Verified the branch point aea472f = #611 (GAP-16), the merged sequence (A1 #606 / GAP-15 #607 / GAP-14 #609 / GAP-16 #611) is accurate, the GAP-16 entry records the Option-B source + the int/mart/DQ/export + the doc-sync fold (deferred to #611's own review.md, not re-decided), and GAP-01 is correctly the sole remaining spec'd Phase-B item with disposition still "pending" (needs a §10 ruling) — no premature closure.
- Governance integrity (the #610 failure must NOT recur): the doc-sync fold-generalization question is explicitly kept OPEN — active_work.md says "NOT decided" + "Each fold was a specific CPO direction, not a general rule" (2 instances recorded: #609 status-only, #611 substantive), and the contract's decisions_reserved reserves it to the CPO. The plan-mode carve-out is attributed to the CPO ("CPO-set 2026-06-30") and bounded to handover/bookkeeping refreshes (full plan mode preserved for code/model/metric). No silent §10 reinterpretation; do-NOTs + the two stale-wireframe flags preserved.

## escalations
(none) — doc-only handover; records this session's post-#611 state and RESERVES (does not decide) the next pick (GAP-01 / Phase C/D), GAP-01's pending disposition, the fold-generalization question, and the two stale-wireframe reconciliations to the CPO.
