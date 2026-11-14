# Review — feat/310-shirt-identity — 2026-11-14

diff_sha256: 83361891d0fdf010b56b5b7dd18b27c33466addfeba22ef699ff87caaa9e0f7f

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged file is in scope_paths; the CPO approval on #310 is named with its date; the engineering guards (one candidate per shirt, per sheet id and per stats id; hand-overridden and researched sheets not paired; substitution events take the pair) are guards inside the approved rule.
- The impact_map carries the 61-model lineage, the marts and a read-only prod measurement (16,589 rows, 7,254 matches, 43 competitions); no new mechanism or recurring cost; no page surface touched.
- base.yml states the rule on the model description and on player_id, in plain words, with no history.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the test excludes hand-overridden ids on both sides; it reads only the fetch base read; base.yml documents the rule; shirt_pairs is unique per shirt, per sheet id and per stats id, so the parsed and substitution joins cannot fan out.
- Layer placement in base, no new stg or mart ref, no cycle (base_apif__fixture_players does not read base_apif__lineups), no competition identifier, no metric or seed change; the grain tests still cover the model.
- Residual noted: a sheet id listed under two shirts would raise a loud false alarm in the test, never wrong data.

## escalations
(none)
