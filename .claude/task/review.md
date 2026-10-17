# Review — fix/218-design-gate-from-main — 2026-10-17

diff_sha256: f111fc6943d504fd300d1589f18225cbf4cecc31e1b77527819b6801df9ccb83

rounds: 2

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard paths: protected_override names the plan's approval, and the impact_map matches the diff (the base-ref condition, the CI check, the label deny removed).
- The changed mechanism is declared as a THRESHOLD and stays inside it: list file, seed without Home, regex parsing, base-ref-only reading.
- Plain git and the standard library; no new dependency; the token read, the requests call and the project id are removed.
- No cost change: CI reads one file from a ref validate:governance already fetches at full depth.
- A branch cannot approve its own page: only `git show <base>:<list>` is read, CI passes the target branch explicitly, and tests pin a branch-only list as refused.
- The merge deny is untouched; the hook's fail-open on a bug is unchanged, and an unreadable list denies.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 found three defects; round 2 closes each: a non-UTF-8 byte in the list no longer fails open, every design on a contract line is checked, and the list parser and the shipped file are pinned by tests.
- Each fix was proven by mutation: reverting it fails its test.
- CI path: `origin/<target>` resolves at full depth; cwd is the repo root; design-only MRs and pushes to main return before the design check.
- `default_base()` delegates to the hook's resolver; its three tests still hold.
- Read-only git calls only; no credential or permission change.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every diff path is in scope_paths; amendments are none.
- The list holds exactly the planned seed; the label deny, the label read and the token are removed, and grep finds them only in task paperwork.
- Both working_agreement.md lines match the approved text word for word; agent_guardrails.md and 00_overview.md match the mechanism.
- The threshold is declared; no new library; the none line is honest, since no page-surface file changes.
- No decision history, dates or chat quotes outside contract.md.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The added overview row and the list carry no metric, label, field or display rule; metrics_display.md is untouched.
- The reading order and the conflict rule are unchanged; the row answers a separate question and its link resolves.
- The seed matches the screen inventory for the Competitions hub, the competition page and the Matches page; the match page's approval stands on its issue and the mocks README, and the inventory does not contradict it.
- Home is left out deliberately, so the list claims no approval the inventory denies.

## escalations
- none
