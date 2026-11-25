# Review — claude/347-statistics-export — 2026-11-25

diff_sha256: ab2dc8aba87ffcc67ceab74c6059131fad2af39f83e30e9e95732281eae6f3ae

rounds: 2

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Both changed lines of the seed (goals_penalty_player 7, contribution_player_pct 8) and the three changed lines of tests/test_catalogue_order.py are byte-identical to the same lines of the reviewed patch of the unsplit branch, which this reviewer passed; a script confirmed that every changed line of this diff is in that patch. No model reads metric_order, so no mart column changes.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- The order was passed in round 2 on the unsplit branch: penalty goals follow goals and share of team goals closes the group after the counts it builds on; positions 7 and 8 are free in the (entity, metric_group, metric_order) uniqueness rule. This MR carries exactly those two seed lines and the pinned order, unchanged.

## fixes
- a metric_order set without its recorded approval | sweep: every catalogue row this change gives a place is the two named in the contract, listed by diffing the seed against main (two rows, no other metric_order moves) | test: tests/test_catalogue_order.py::test_the_catalogue_order_is_pinned_per_group_for_players_and_teams

## escalations
(none)
