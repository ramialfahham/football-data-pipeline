# Review — fix/247-keeper-goals-against

diff_sha256: 2c495c2409cc8c0b43c3a5fccaa377d617d661fb333577be832ca0bb5eba2c41

rounds: 4

rounds_cap_override: approved in chat, 2026-11-04: one more round, for the test exemption and the rule text fixed after round 3.

## scope-auditor
VERDICT: PASS
risks_checked:
- All four changed files are in scope_paths; no amendment was needed.
- The rules in the diff match decisions_taken; nothing in decisions_reserved is decided; no new mechanism or recurring cost.
- The impact map carries the pasted lineage, the readers of the column and a counted blast radius; the change fills blanks and narrows no coverage.
- cleaning_rules.md moves with the code; no stale reference to the removed columns; approved_design none holds, no site or export file is touched.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Rounds 2 and 3 FAIL closed: a keeper with no minutes data keeps a blank rather than a 0, and the test exempts only keepers who played without being the sole keeper of a whole match; the rule text states when the value stays blank.
- Layer placement, grain and fan-out: the new CTEs sit in base, read only inputs the model already read, and cannot duplicate rows.
- Event semantics against base_apif__fixture_events: subst and Card literals, own goals under the benefiting team, shoot-out kicks outside is_goal, a null-minute goal and a goal in a change's minute both leave the value blank.
- Test and model agree case by case; the answer-key rows cover both fills and the same-minute blank.
- Residual risk for the blank-line report: a keeper whose substitution event is missing but who has a later card would count from kick-off; no evidence it occurs.
