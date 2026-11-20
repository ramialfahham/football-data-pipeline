# Review — claude/231-check-counts-35b082 — 2026-11-20

diff_sha256: b854813fa80b724f127da0e5a6efb9b360af8c73f2ce879e1f0afcf2efef44ff

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- All changed files and the contract are inside scope_paths, no amendments; no page output changes.
- The registry key `breaks: hyphens` and the new presence conditions are declared in decisions_taken with their approval; thresholds are read from the page code.
- The three baselines only lose the Matches day page miss pins; no pin rises.
- The Fold, Match row score and Filter row expectations are gated by a precondition read from the rendered rows, so the change narrows nothing a defect could hide behind; tests keep each still-counted case.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Four protected paths are touched; the contract carries a named protected_override and an evidenced impact_map. The MR head must list the four locked files.
- The hyphen exemption applies only to registry parts marked `breaks: hyphens` (only `.club`), needs every break after a hyphen and a word wider than its line; the presence conditions copy the page code's own thresholds.
- `breaks: hyphens` is a new value of an existing key and PRESENCE_NEEDS a conditional inside the existing check: no new dependency, service, workflow step, run cadence or recurring cost.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL on two findings: the score precondition read the nodes it excuses (fails open), and the every-break-after-a-hyphen rule had no test. Both are fixed in round 2.
- Round 2 delta: a row with other than two score spans falls back to its own `played` class, so a played row that lost its score spans is a miss again; a test covers it and fails on revert.
- Round 2 delta: a hyphenated word also broken inside a segment still counts as a split; a test covers it and fails if the every-break clause is removed.
- The check stays fail-closed: the fallback only adds cases where an element is expected.

## escalations
(none)
