# Review — claude/313-context-guard

diff_sha256: e665f4a87415b8adcc767ce3e0c5e0e6208119470611e2a9e4115eda02a6f56e

The hash is rebound with no further round, approved in chat, 26 Nov 2026 (issue 313). The reviewers
passed it as 93b51748717ee5d4a26a8bee09f54edc97086909482b63fa4425608536b243e1. Main 40e2b1a6
changed other lines of docs/agent_guardrails.md; the lines this branch adds and removes are the same.

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2 delta (corrected impact_map and decisions_taken wording, one added sentence in the block text, tightened tests) does not widen the surface; the round-1 PASS stands.
- Scope, protected_override naming the approval, declared new mechanism, no recurring cost, no page surface, doc row in the same branch: no defect.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the contract now states that a Stop block makes the next Stop skip stop_gate.py once per session, and that the hook imports read_event from _command_utils (11 importing files confirmed by grep).
- Ruling: the once-per-session unchecked hand-off turn is an engineering call, not a loosened guard invariant. The tree is checked at the turn end before the block, the block text limits the hand-off turn to the state file, and the commit gate and CI stay fail-closed.
- Fail-open on every error path, no dependency, no recurring cost, no secret or permission change in settings.json: no defect.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the interaction is stated in the contract and in the block text with a test pinning the text; the synthetic, sidechain, zero-usage, role and type filters are each pinned by a test that fails when the filter is removed.
- Tail read, exclusive-create marker, session id sanitising, test isolation through TMP and registration in settings.json unchanged since round 1: no defect.

## fixes
- false statement about what the code does | sweep: every claim in the contract's impact_map was checked against stop_gate.py and the hook's imports | test: tests/test_context_guard.py::test_the_block_tells_the_session_to_edit_nothing_but_the_state_file
- entry filter no test pins | sweep: each filter in the hook (type, role, sidechain, synthetic model, zero usage) was matched to a test entry that fails without it | test: tests/test_context_guard.py::test_sidechain_synthetic_and_zero_usage_entries_are_skipped

## escalations
(none)
