# Review — fix/232-goal-check-scorers — 2026-10-25

diff_sha256: 76a666b1f2998bc3ce9b44fd874c761f4cf917b584fb1a679df0c23fc56ea182

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Only the contract and assert_result_corrections_applied.sql change, both in scope_paths; the rule matches the approval recorded in decisions_taken and on the issue.
- The added-minute reading is declared in the contract and adds no mechanism, dependency or cost.
- The other branches and seeds' checks are unchanged; approved_design is empty and no page output changes.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Both goal-key steps normalise the added minute and join on plain equality, so each key is unique per side and least() caps the match one to one; goal_matches is one row per match.
- A seed goal without a player id or minute never matches, so its correction stays needed; a fully matching provider is reported no longer needed.
- not_applied, does_not_add_up, not_sourced and the other two seeds' checks are untouched; the new condition only narrows the last case.

## escalations
(none)
