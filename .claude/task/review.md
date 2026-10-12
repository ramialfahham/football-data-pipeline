# Review — feat/lineups

diff_sha256: ba28172d651157de7de3d25b1210212560b4b246b201af31b761e882b8e21e60

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged path is inside scope_paths; the seed ships header-only, so the research rows stay reserved, and the metrics switch, the page and export and the player-match mart merge are untouched.
- Every decision in the diff carries a named approval in decisions_taken: the line-up states, the checks, the substitution rule, the shirt and position precedence, the researched-line-up exemption from the squad lists, the squad-list rule, the research priority and the nightly cost; the same-season club reading and the walkover exclusion are recorded as readings.
- lineup_state takes only the three approved values in every layer.
- Section 10 thresholds: no new mechanism; the recurring cost is measured and accepted; Appendix A: nothing found.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: parsing, the seed and the checks sit in base; the core fact projects onto surrogate keys and reads no JSON; the marts select, filter and join; no league code is hardcoded.
- Grain: fct_fixture_lineup is unique on (fixture, team, player); the mart's join on (fixture, player) can double a row only for a player on both sheets, which makes the match not_available, and the grain and stat-line tests catch the rest.
- The checks fail closed: eleven distinct starters with ids, the squad-list rule with the transfers where no squad list exists, no player on both sheets, no stat-line team clash, and every substitution paired from both the sheet and the event side on the same team.
- Tests: error tests judge only shown line-ups; the research list is warn-only; every researched seed row's source is validated.
- Evidence on prod: 53,942 confirmed and 6,254 not_available played matches; every old stat-line row kept with no value changed except starter and substitute and 175 blanks filled; the momentum mart's stat coverage unchanged.

## escalations
(none)
