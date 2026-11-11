# Review — claude/289-result-row-ha

diff_sha256: a5c3a60a772a17bc79f47c2433ca64f2a4680142e7dfc1db7b1af4ea7137a9ff

rounds: 5

rounds_cap_override: the reviewers' registry, history-pin and row-level fixes, and round 5 for the re-rendered comparison pins only, approved in chat, 2026-11-11

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; components.yml carries protected_override; each amendment names its authority, the #132 header deviation included.
- Match, Team and Player designs cover every page the diff changes; nothing reserved is decided.
- The registry and block standard texts match; no doc still states the 420px switch for result rows; no issue number in ruled-on values.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every rendered value is an existing field; each row shows exactly one home or away in every state, with and without the script.
- Each Match column is its own list, and the subgrid keeps row by row level; Head to head and goal rows keep their own switch.
- No middle dot ends a result-row meta line in either form; the header under 700px carries no line between the teams.

## cto-reviewer
VERDICT: PASS
risks_checked:
- No new mechanism: the fit marks and the "rows" measure are reused; the Fitted block assertion is widened, never weakened.
- components.yml changes are additive and approved on #289; no other guard path is touched.
- No dependency, workflow, credential or recurring cost.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The two comparison pins are CI's Linux renders; the manifest changes only their two hashes and stays linux.
- The delta touches only the two PNGs, the manifest and the contract's scope line and amendment.
- validate:ui runs check_chart_screenshots.py against these pins on Linux and fails closed on any mismatch.

## escalations
(none)
