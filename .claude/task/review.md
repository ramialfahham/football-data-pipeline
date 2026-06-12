# Review — governance/g4-alignment-audit — 2026-06-12

> Step 4 (Lock). G4 audit, COMMIT 2: the CPO-rulings update (the per-finding
> decisions table). Required reviewer for `docs/audits/**` = scope-auditor.
>
> Iteration note: the first faithfulness re-run returned FAIL — a FALSE positive.
> The blinded scope-auditor read the stale `.claude/task/review_input.patch` (left
> over from the #405 model-pinning task, already merged to main) and mistook those
> agent/routing changes for this diff. The actual staged diff is only the audit
> doc. Fix: `review_input.patch` was regenerated to the true staged diff; the re-run
> then PASSed. (Workflow defect logged: the cycle must refresh review_input.patch
> before each blinding — second haiku miss this session after F39.)

diff_sha256: 9f1a5be957819818897628c806a01f2ff8fd9ba5085be484842723d18fc33990

## scope-auditor
VERDICT: PASS
risks_checked:
- Frozen-item enforcement (F8/F9 / GAP-17): verified the two same-window violations
  in shipped MVP metrics are recorded as frozen (GAP-17, "do not act") and isolated
  from the action-issue set (#409–#427) — no work issue filed for them, honoring the
  contract's decisions_reserved freeze on shipped numbers.
- Parked-ruling isolation (F5-spelling, F7, F38): verified the three reserved-Pilot/
  #391 items are routed to #391/Pilot and do NOT appear among the action issues; the
  F5 row correctly splits migration (→GAP-19) from the parked transliteration
  spelling, keeping the reserved slug ruling out of action.
- Ledger fidelity: all 40 findings present; every row's ruling matches the session
  ledger; no builder-invented, dropped or altered ruling; F39/F40 remain no-action;
  no violation silently downgraded.

## escalations
(none — faithfulness PASS on the corrected diff.)
