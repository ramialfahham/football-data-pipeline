# Review — feat/goals-on-match-mart

diff_sha256: d0ea5824e8937d69450195e6855df2dc0a7186308b4770d42e90968d52f7df63

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file is in scope_paths, the result-corrections seed and its test by the recorded amendment; the goals list, the states, the award columns, the new seed and the goal-source order are in decisions_taken; nothing reserved (#175, CAF 1619054, the mart renames) is touched.
- The impact map pastes the 67-model lineage of both seeds and a blast radius that names the 42 goal-corrected matches, the 20 score changes, the 8 walkover winners, the 11 status changes and the 23 award kinds; the 151 seed rows match it.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The goal seed is applied in base like the other correction seeds; the union aligns column by column; replaced provider goals stay uncounted, seeded goals sit at event_index 10000 and up, and the latest-fetch test skips only them; the mart stays one row per fixture.
- Tests ship with the change: the seed's grain and value tests, the extended corrections test, and the new mart test (state, adds up, minutes, unknown player, unreconciled goals); the hand-checked side tallies of the seeded matches add up, own goals under the side they count for.

## escalations
(none)
