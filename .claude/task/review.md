# Review — chore/handover-program-structure — 2026-06-23

> Documentation-only handover restructure into the CPO-approved two-track operating model
> (PRODUCT primary + PROGRAMS coverage #545 / data-quality #546 / cost #547). Brings the status
> current and sets next actions by track. Scope: .claude/active_work.md + .claude/task/**.
> Routes to scope-auditor only; contract.md hashed (non-exempt), active_work.md hash-excluded.

diff_sha256: 6d1e9dd11d0da87322ebb68deeb3fd448832ecd8adb402cf5930ef5066981bfc

## scope-auditor
VERDICT: PASS
risks_checked:
- Pre-decision of the #526 canonicalization fix (Appendix A6 spot-fix drift): the handover states the
  investigation diagnosis (provider duplicate-team-id; data complete/uncorrupted) but explicitly keeps
  the FIX "STILL OPEN — decision pending on where/how to canonicalize." The layer choice is deferred to
  the CPO, not smuggled into diagnosis prose. Held — no spot-fix drift.
- Pre-decision of the coverage-tranche cut (Appendix A6 coverage-cut framing): expansion (#545) is
  framed as "CPO picks the first tranche," not a foregone conclusion or a DQ-justification; the
  diagnosis explains the program while the choice stays CPO-gated. Held. Also confirmed: both changed
  files in scope; the two-track model + epics are recorded as CPO-approved ("Do it"); no §10 smuggled.

## escalations
(none)
