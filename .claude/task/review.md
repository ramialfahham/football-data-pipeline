# Review — feat/218-approved-design-gate — 2026-10-17

diff_sha256: 9bda6ee7ed5c4cdf9ae50b3d2e63a6539bd4c2284a2f098c3f1a7e86a1f5caf2

rounds: 2

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanism and credential: the approved_design gate and DESIGN_GATE_TOKEN are declared as a THRESHOLD with their approval; protected_override and a real impact_map cover the hook and agent edits.
- Round 1 escalated two questions; both are answered and recorded in decisions_taken and amendments (see escalations).
- The label block sits beside the merge block, reads the unstripped commands so quoted labels are seen, and its residual (other glab api spellings, non-glab clients) is declared best-effort.
- The hook keeps its fail-open house rule; CI fails closed on a missing token, a non-200, a request error or a bad body.
- No new dependency (requests is pinned); one API read per named issue; validate:governance is not scheduled.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 found three untested paths; round 2 pins each: the block closure (an issue number after an empty or placeholder block still denies), the CI wiring end to end through main(), and the fetch's 401, 404, bad-body and request-error branches with the URL and header asserted.
- Each pin was proven by mutation: with the closure, the wiring or the status check removed, its test fails.
- The label deny matches quoted, encoded and any-case spellings and allows only glab issue list and view.
- Artifact-only MRs and pushes to main return before the design check; importing the hooks from CI has no side effects.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every path is in scope_paths; git_discipline.py joins by a dated amendment naming the CPO's answer, and protected_override lists it.
- The diff builds only the plan and the two answers: the field, the page surface, the label check, the token read, the label block, hunt item 10 and the docs.
- Thresholds are declared; decisions_reserved (which issues get the label) is not decided in the diff.
- No credential, no decision history, no rationale in the doc text.

## escalations
- question: May the agent set design::approved itself, or must a hook deny it?
  CPO ANSWER: answered in chat, 2026-10-17: block it in the git hook beside the merge block, stated as best-effort.
- question: Is a "none: no page output changes" line checked only by scope-auditor acceptable?
  CPO ANSWER: answered in chat, 2026-10-17: accepted, and named in agent_guardrails.md as the gate's weakest link.
