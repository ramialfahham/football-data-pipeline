# Review — test/metric-answer-key — the metric answer key, the two reconciliations and the ranking floors as vars

diff_sha256: 1ee38ed09b200acc544310ed7c8a5823c4da3d560c6b1e9ff850e1210ff322a2

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every diff file is in scope_paths, the deleted macro listed explicitly; the round-2 amendment adds dbt_project/docs/layering.md with its date, authority and content, and matches the layering.md edit exactly.
- Section 10 and Appendix A: no catalogue row, formula, window, label or display text changes; the wireframe line swaps the macro name for the model name only; the floors 270, 10 and 3 are copied from the old literals; floors as vars rest on the CPO's step 5 answer quoted in decisions_taken.
- Thresholds: NEW MECHANISM none (vars, seeds, singular tests, an intermediate model); RECURRING COST declared as four tests and one small model, measured and put to the CPO with the MR.
- Impact map evidenced: the dbt ls selector, the 8-model list, the git grep for the macro and the read-only prod measurements; no coverage cut; no secret, permission or workflow change; no escalations.log entry.
- Round 2 delta: the table's own points checked in the one direction no deduction explains is a reading inside the delegated right, recorded in decisions_taken and the amendment; layering.md:334 now names the long model and drops the literal floor.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the macro becomes int_player_competition_benchmark_metrics_long in 4_intermediate, reading only int_player_season_position__metrics; the engine and the mart read it, mirroring the team long model; no materialisation set.
- Behaviour equivalence: the macro's position eligibility, finishing floor, numerator and denominator expressions and the null filter map one-to-one onto the new struct list and its WHERE; the mart's rank and percentile partitions and join keys are unchanged.
- Vars and seeds as config: the three vars sit outside the generated league-code block that sync_dbt_vars.py rewrites; both seeds have column types, a grain test, not_null tests and a description on every column.
- The four singular tests: columns exist on the relations read; error severity with store_failures; the answer-key tests fail on a metric outside the catalogue, a metric not on the model and a missing row, and compare with is distinct from; the goals exclusion errs toward failing.
- Competition-agnostic: no competition identifier in the new SQL; competition codes appear only as seed data.
- Round 2 delta: the league-table test also fails on table points above 3 x wins + draws or blank, inside the existing WHERE with no join or grain change; layering.md:334 names the new model and drops the copied floor.

## platform-reviewer
VERDICT: PASS
risks_checked:
- tests/test_ranking_floors.py against the real ranking_rules text: whitespace normalised, the substring checks not fooled by prefixes, and the only digits in the block are the three vars.
- The literal-floor scan covers 4_intermediate and 5_marts, cannot pass vacuously, and would turn red if any of the six floor sites went back to a number; base's minutes >= 90 and the team ranking's >= 1 are outside it by design.
- Var presence and type, and the var() regex matching both the {{ var() }} and the string-built form in mart_leaderboards.
- CI collection by test:python and the PyYAML dependency already pinned; no requirements, workflow or hook change; the test is read-only and deterministic.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The only display-facing file is docs/wireframes/12_player_stats.md:146, which names the new model as the 18-metric set's home; no user-visible string, label, format, order or tier changes.
- The new model holds the same 18 keys with the same position eligibility (GK 4, outfield 16), so the wireframe's set and its lists stay true.
- The five ratio metrics keep the numerator and denominator behind the {num} of {den} · {pct}% triple; per-90 metrics keep both NULL; rows without a value are still excluded, never turned into a zero.

## escalations
(none)
