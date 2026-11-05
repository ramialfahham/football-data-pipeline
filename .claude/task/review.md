# Review — fix/247-sole-keeper-score

diff_sha256: c4954873fa444b09acd2b57308d96e8842555b026422562e884a8ad17ed459ae

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- All five changed paths are in scope_paths; no amendment was needed.
- The rule extension is recorded as approved in the contract; no new mechanism, metric, label or recurring cost.
- cleaning_rules.md, the answer-key seed and the cleaned test move with the model; approved_design none holds, no site or export file is touched.
- The impact map carries the lineage, the readers of the column and a blast radius that fits a one-line model change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Model case by case: a null filled value or score returns first, the multi-keeper branch is untouched, the sole keeper gets the score at any gap, every other case keeps the limit of 2.
- Null handling: a null score stays blank in the model and is skipped by the test's guard; the test now flags a blank sole keeper where the score is known.
- The minutes basis of model and test selects the same rows; the correction stays listed under matched_to_team_goals_conceded.
- The two answer-key rows follow the new branch, checked against the rule text and logic, not warehouse data; no other test pins the old blank.
- Logic stays in base; no metric, competition identifier, frontend or export change.
