# Review — feat/235-points-rules — 2026-10-28

diff_sha256: e87f1ec3cc8deac3940afe52c85e53ee59b48efe94a848936d1f3b1218867677

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; refs quote the approved R3 sentence, the points_won texts and both formulas.
- Deductions stay reserved; no new mechanism, dependency or run cadence; no export or frontend change.
- The test changes follow the shoot-out rule without hiding a defect.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The flag reads int_round_names on its grain, so legs cannot fan out; it is not null and tested to be a draw.
- The league-table test compares our points with the table's plus points taken; a warning test checks every ranked team's points against the table.
- A season the results do not reproduce is dropped, never mis-ranked, and ranking stops at the table's matches played.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- A table shoot-out win is a draw worth 1 plus 1, so 2 points; the loser keeps 1; cup and play-off shoot-outs are unchanged.
- points_capture_pct stays at most 100 percent over the same matches.
- The description, the interpretation and the formula agree; each column holds one thing.

## escalations
(none)
