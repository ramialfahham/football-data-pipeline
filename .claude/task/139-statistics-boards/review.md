# Review — feat/139-statistics-boards — 2026-11-13

diff_sha256: 182d58369f387d4c605c8d5f1c1c9f549d2a385abe256b41e2a107ef3111af5a

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL, three findings: the number rule, the 7/8 Goals order and two board scopes rested on no named CPO approval.
- Round 2: the number and ties rules cite the CPO on #230 with dates; rounding is stated as BigQuery's ROUND, an implementation detail; the 7/8 orders are blank as on main; goals against for keepers cites the #139 design; dribbles_past_per90 follows the plain per-90 rule with its consequence stated.
- Every diffed path is in scope_paths; approved_design names #132 and #136 for the only two site_v2 files, both reorders pinned by the metric-set test; the new seed and the read growth are declared thresholds.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the contract did not quote the four new catalogue rows; round 2: the quoted rows match the committed seed field by field, each with its source.
- Layer placement, join grain of int_player_profile__contribution, the team mart's board columns in int_team_season__metrics_cumulative, the same-window pairing of every percentage floor: no defect.
- Tests: floors and the 44-board count, rank ties on the shown value, the display_value recompute, the difference board, the updated leader-order and match-board tests; the comparison sets pinned at 34 and 24.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: metric_order 7/8 in the player Goals group had no CPO approval; round 2: both blank as on main.
- The four new rows: formulas match their twins, descriptions in the per-90 form, directions per the schema rule, orders unique per (entity, group).
- No existing row's description, formula, format, direction or label changed; only metric_order cells.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The board lists parse to 44 season boards (15 counts, 21 per-90, 1 scoped, 7 percentages) and 8 match boards, agreeing with shared.yml, the floors test and tests/test_leaderboard_board_sets.py.
- The decision-history pin moves 281/95 to 273/93, exactly the eight flagged comment lines the rewrite removed; no new flagged line.
- Re-run safety, generated SQL against the generator lists, the new seed's codes, no hook, workflow, dependency or credential change.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Both JSON files are exactly what the export emits from the new catalogue: 34 and 24 rows, the same sets as on main, in the CPO-approved order.
- Count before percentage holds in every group of both files; no label, string or locked bundle row changed.
- Round 2: the two cleared orders never fed either file, so both are unchanged.

## escalations
(none)
