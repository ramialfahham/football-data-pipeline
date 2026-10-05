# Review — test/table-points-adjustments — a league table's points below its results are explained by a declared adjustment

diff_sha256: 6f96815fffc7fc868ac171c1fde12e49fc7afad03235922d5c29a5be6ca4ce4e

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the seed, schema.yml and the test are in scope_paths; no amendment; no impact map required (seeds and tests only).
- The test condition is tightened, not narrowed: a blank table total and an undeclared lower total both fail; the join, the played filter and severity error are unchanged.
- Section 10 and Appendix A: no metric, label or display change; the seed follows the standings_corrections pattern; readings under the 2026-10-02 delegation.
- Thresholds: no new mechanism, no new run or cadence; the 52 rows match the acceptance criteria; every row has an https source and match_reports rows two sites; no secret or workflow change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement and competition-agnostic SQL: a seed and one singular test over core and intermediate; no league identifier in SQL.
- Seed arithmetic: 38 Belgian rows plus 14 deductions; points_taken equals half the regular-season points rounded down in all 38 halving rows.
- Test condition: null-safe, catches an undeclared lower table, a fixed table whose declaration no longer matches and a blank total; the same-window join unchanged.
- Round 1 FAIL, two findings: the source description stated a format rule no test enforced, and nothing stopped a zero or negative points_taken from letting a table above 3 x wins + draws pass.
- Round 2: the description no longer claims the format rule; a seed-level expression_is_true holds points_taken at least 1. Both resolved.

## escalations
(none)
