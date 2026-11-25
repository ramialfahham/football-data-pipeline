# Review — claude/350-proof-rule-0e7e56 — 2026-11-25

diff_sha256: 7c33797860d123d707a2f718936a99b9925f46895b7c38c271213c1506829914

rounds: 1

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanism: `## closed`, `_proof_error`, `_closure_gate` and the hidden-FAIL count are checks inside the existing commit gate and its CI backstop, declared in decisions_taken with issue #350 as the authority; no new hook, package, service or CI job.
- Guard invariants: the hook still fails open through the `_commit_gate` try/except; `validate:governance` still fails closed. A FAIL in the preamble, `## fixes`, `## closed` or `## escalations`, or hidden by a duplicate header, is refused.
- Guard loosening and its authority: a FAIL can now be cleared by a `## closed` entry whose reason nothing verifies; this is the issue's rule, declared in the contract and approved by the merge of the quoted MR head.
- Round cap 3 to 2 tightens the cap and adds no recurring cost; deploy_order covers a branch at `rounds: 3`.
- Protected paths carry protected_override and a non-placeholder impact_map; routing, settings and `.gitlab-ci.yml` are unchanged. No dependency, cost, credential or undeclared-threshold change.

## platform-reviewer
VERDICT: PASS
findings:
- [nit] fail-open blind spot in the hook tests: tests/test_reviewer_standard.py test_a_closed_finding_needs_no_proof, test_a_closed_fail_commits, test_round_two_commits_and_round_three_needs_the_cpo — the hook-side commit checks assert only `not denied(out)`, so a crash in `_closure_gate` (the hook fails open) would also read as a commit; the unproven-but-closed case has no CI twin.
risks_checked:
- Re-run and interruption safety: the new functions are pure over the review.md text, with no writes or state.
- Guard mechanics: the hook fails open with the "COMMIT GATE ERRORED" context; `check_task_artifacts.py` propagates an exception and CI fails closed.
- Removal of the global FAIL check: a FAIL with an open blocking finding, under `## closed`, `## fixes` or the preamble, or behind a duplicate header is still refused; the count check cannot under-count.
- Closure order: the proof exemption uses `_closed_pairs`, and `_closure_gate` then refuses a placeholder reason, a malformed entry or a class the reviewer never reported.
- Proof parsing: every refused shape in P3 and P3b traced through PROOF_RE and the two fullmatches; a second ` | proof:` fails safe.
- One copy of each rule: CI calls `_gd._findings_gate`, `_gd._closure_gate` and `_gd._rounds_gate`; no other script re-checks the FAIL string or a cap of 3.
- Reverting each change fails a named test; the template examples match FINDING_RE, the proof check and CLOSED_RE.

## escalations
(none)
