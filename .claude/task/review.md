# Review — chore/243-protect-design-checks

diff_sha256: e57ab7f5bf6ca8cd22be1d4ac9ab69551d9e935b66c390ad0edf1a0d949abfc4

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every patched file is in scope_paths; tests/test_sentence_length_in_docs.py is covered by a recorded amendment and its pin only falls, 20 to 19.
- protected_override names the approval and its date and the four paths; the impact_map is evidenced with line references and now discloses the out-of-scope exemption.
- decisions_taken declares the recurring cost with its measurement and no new mechanism; decisions_reserved is none and the diff decides nothing outside it.
- Every document states 13 guard paths, 7 shared with platform, 6 the CTO reviews alone and 16 CTO rows; no stale count remains.
- No secret, workflow, CI, site_v2/src or export change; approved_design none is honest.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL closed: the impact_map now states that only the PreToolUse Edit and Bash-write paths refuse the edit, that check_task_artifacts.py never calls _is_protected, and that CI's cover is the routing rows.
- The out-of-scope exemption at stop_gate.py:170 and task_contract_gate.py:691 now covers the four files in any task with protected_override; it is the existing meaning of a protected path, it is disclosed, and the CI reviewer check still requires both verdicts.
- The guards get stronger: an ordinary task cannot edit the four files even with them in scope, and a governance task needs an impact_map; the hook still fails open on data-only entries.
- No new mechanism, no dependency, no credential; the recurring cost is declared with a measurement and its approval.
- baseline.json staying ordinary holds: compare_counts fails any pin that differs from the measurement and the protected test refuses any pin above main's.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The hook change is four data entries; every caller of _is_protected picks them up, and main() still fails open; CI fails closed through the new routing rows.
- Reverting the change turns the new hook test, the four impact_map cases and the four PINNED_CASES red; dropping platform from a row is caught by the parity test's shared-set assertion.
- Every COUNT_SITES anchor matches 13, 7, 6 and 16; thirteen is in NUMBER_WORD; the removed HISTORICAL snippet no longer occurs and its replacement matches no claim shape.
- The PROSE_SUBSETS entry excuses only the platform brief's territory sentence; a stale count there is still caught by its anchor.
- The sentence-length pins are consistent with the split sentence.
- Round 2 changed only the contract's impact_map and three message strings in the parity test, all text, after this verdict.

## escalations
(none)
