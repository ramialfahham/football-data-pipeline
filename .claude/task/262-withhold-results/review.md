# Review — claude/262-withhold-results — 2026-11-15

diff_sha256: 93246241195b8314eb59bd57e226ac3c5b03dfcc1fe45b5c59f8f5c65a6a02ff

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file lies inside scope_paths, mart_player_fixture_stats.sql included after a clean-tree amendment (decision 6).
- The seed is !442's blob b1bdc04b: the eleven appended rows only.
- Reserved items are untouched: the five other provider checks, assert_extra_time_goals_counted_in_score, the site label and export, and the shoot-out of 1647990.
- No test is weakened: the PEN not_null tests and the finished-goals test exclude flagged rows. New error tests require a flagged result blank and a flagged match not played; the result not_null covers rows with a score.
- Tests of our own code are unchanged: winner_follows_the_result, the winner and award keys, and award_kind.
- No new mechanism: the cards_need_research pattern inside the existing base model.
- cleaning_rules.md states only current behaviour; no "awaiting result" and no daily-list claim.
- No cost or cadence change, no credentials, and no unrecorded §10 decision.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The flag is the union of the replaced tests' conditions on the corrected values, coalesced to false, with AWD and WO excluded.
- assert_result_corrections_applied: status and award comparisons run on every row; goals and shoot-out comparisons only on unflagged rows, fully parenthesised.
- Unflagged values are unchanged: the cleaned CTE keeps the earlier expressions, and fct_fixture selects by name.
- int_legs__team_match readers already need both goals. int_knockout_ties now counts a leg as played only with both goals, so a withheld leg leaves its tie undecided.
- mart_player_fixture_stats keeps every row; result is NULL where a goal is NULL, and its readers do not use result.
- Layer placement: cleaning in base, passed by core, served by the mart; no hardcoded competition; descriptions under 1,024 characters.
- Non-blocking: a fixture_goal_corrections row on a flagged match would fail does_not_add_up, and a withheld final would fail the one-winner test. Neither is reachable today.

## escalations
(none)
