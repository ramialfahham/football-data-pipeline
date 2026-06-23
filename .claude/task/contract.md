# Task contract — Handover refresh (#526 closeout, 2026-06-23)

objective: >
  Refresh .claude/active_work.md after the #526 closeout: PR #551 MERGED (the fixture-event
  team-attribution fix; resolves #526, now CLOSED), and the FALSIFIED "provider duplicate-team-id
  quirk; data complete/uncorrupted" framing corrected to the verified two-class finding
  (Togo 6424/25274 = two distinct clubs / mis-attribution; Riga 2263/10124 = one club / duplicate
  id). Record the new follow-ups #549 (proposal-phase gate) + #550 (automated DQ triage design).
  Doc / bookkeeping only — no code, no product decision.

refs: >
  This session 2026-06-23. Merged #551 (resolves #526). Filed #549, #550. Memory:
  feedback-verify-real-world-identity.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation-only handover refresh. No code, no §10. The commit carries contract.md (hashed, not
  artifact-exempt) so it needs review; routing for active_work.md + .claude/task/** is scope-auditor
  only. active_work.md is hash-excluded (artifact). All facts recorded were established and
  CPO-actioned this session (the #526 re-diagnosis verified externally + triple-confirmed, the #551
  merge, the #549/#550 filings).

decisions_reserved:
  - none. Pure handover bookkeeping. The #545 tranche cut, the #549/#550 designs, and the #546
    automation remain open on their own issues — not decided here.

done_when:
  - active_work.md status reflects: #551 MERGED / #526 CLOSED; the corrected two-class #526 finding
    (NOT a duplicate-id quirk); #549 + #550 filed; main GREEN.
  - The stale "provider duplicate-team-id quirk; data complete/uncorrupted" framing is removed.
  - Tree matches the contract (only active_work.md + .claude/task/**).

amendments: (none)
