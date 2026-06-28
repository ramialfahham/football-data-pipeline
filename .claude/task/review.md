# Review — feat/team-deserved-vs-actual — 2026-06-28

> Machine-checked review artifact (G3). All three required reviewers (scope-auditor,
> analytics-engineer-reviewer, football-analytics-expert-reviewer) returned PASS on a fresh
> blinded run against the staged diff below. Earlier rounds: analytics-engineer FAIL (two test
> gaps — fixed: sot_rank_gap null/arith invariant + team_season_sk unique-at-source);
> football-analytics FAIL x2 (nullability clauses missing — fixed: all 4 catalogue rows now
> carry a 'Null when...' clause, CPO-approved). Re-run fresh on every hash change.

diff_sha256: 10eec79023e7e40de08443fb9fba619ebef7549bc7338100b3f917615f4a8952

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope/decision-rights: every staged edit is within contract scope_paths; no §10 decision beyond decisions_taken (the 4 catalogue rows, names, gap display, build scope, full-table edge case, method, and the formula-vs-availability ruling are all CPO-recorded). The two added dbt tests are in-scope hardening of files already under change.
- Full-table coverage gate + left-join correctness: both upstream tables are full-refresh with uniqueness guarantees (max 1 row per team-season), so the COUNTIF coverage counts do not double-count; the gate nulls deserved_rank/sot_rank_gap for every team in a non-rankable league-season — correct per decisions_taken #4. No hardcoded competition filter; the standings join generically restricts the read to competitions with a full league table.
findings:
- none

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Same-window rule for sot_difference: the gate requires BOTH games_with_sot_stats = games_played AND games_with_opp_sot_stats = games_played before dividing (shots_on_goal - opponent_shots_on_goal) by games_played; the numerator components and denominator share one game set. shots_on_goal_against_per_match gates on opponent-SoT coverage. No mismatched-window ratio.
- Drift guard + blast radius: the two new OUTPUT metric columns (sot_difference, shots_on_goal_against_per_match) are catalogued (entity=team); the raw upstream columns (opponent_shots_on_goal, games_with_opp_sot_stats) are consumed inline but NOT in the final SELECT, so assert_no_uncatalogued_season_metric passes; downstream marts incl. the LIVE mart_team_season_insights select explicit columns, so the additive columns do not reach the live JSON. Layer contract satisfied (no mart_* ref). Tests adequate (grain unique at source, sot_rank_gap null/arith invariant, no uniqueness test that would fail on rank() ties).
findings:
- none

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Formula resolvability: sum(shots_on_goal - opponent_shots_on_goal) and sum(opponent_shots_on_goal) resolve against int_legs__team_match (shots_on_goal line 116, opponent_shots_on_goal line 123); count(*) valid; deserved_rank/sot_rank_gap correctly blank-expr (the league_rank precedent).
- Formula-vs-availability compliance: all *_expr are pure aggregates (no coalesce/countif/null-gate); per-match denominator = count(*); coverage gating lives only in the model CASE statements. The 'Null when...' clauses are description prose only.
- Nullability honesty: all four rows now carry an explicit null-condition clause consistent with catalogue house style (shot_accuracy/save_ratio), matching the full-table gate behaviour.
- Direction/lower_is_better coherence: sot_difference higher_better; shots_on_goal_against_per_match lower_better; deserved_rank lower_better; sot_rank_gap neutral ('a narrative, not good or bad') — all football-correct and internally consistent.
findings:
- none

## escalations
- question: A blinded football-analytics finding held that the new coverage/rank-gated catalogue descriptions must declare their null condition (catalogue house style: shot_accuracy 'Null when shots_total is zero'; save_ratio 'Null when no save-covered games'). Adopt the convention (edit CPO-approved copy) or override the finding?
  CPO ANSWER: Adopt — "Add the null clauses." Applied to all four new rows (sot_difference, shots_on_goal_against_per_match, deserved_rank, sot_rank_gap); description prose only, *_expr unchanged.
