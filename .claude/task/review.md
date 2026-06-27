# Review — refactor/team-benchmark-demacro — remove team_benchmark_metrics macro (COMPOSE)

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set: always → scope-auditor; `dbt_project/**` → analytics-engineer-reviewer.
> Number-preserving refactor: the team_benchmark_metrics() macro is replaced by one shared long-form model
> (int_team_competition_benchmark_metrics_long) that the benchmark engine aggregates and the benchmark mart
> ranks. dbt CLI broken locally + dbt MCP unavailable — the analytics-engineer SQL review is the pre-CI gate;
> CI's dbt build + benchmark DQ tests are the final number check.

diff_sha256: a41ab0218803c39c939e966ab550450140c9673c50c99a662d4732f5e8ccf495

## scope-auditor
VERDICT: PASS
risks_checked:
- UNPIVOT metric set + null-handling parity: the new long-form UNPIVOT lists all 20 metrics in the same
  order as the deleted macro; UNPIVOT EXCLUDE NULLS (default) matches the prior `where metric_value is not
  null` filters (kept defensively in both consumers); the engine grouping keys + the mart ranking window are
  unchanged — so the numbers are equivalent by construction, not asserted.
- Output contract + materialization preserved: the mart grain (team_sk, season_sk, metric_key), its full
  column set, and its materialization (view) are unchanged; the engine stays a table; layering.md is updated
  to reflect the new composition. No §10 decision (no metric/label/format change, no output-contract change,
  internal-convention model name); player_benchmark_metrics + the dormant scaffolding macros untouched
  (decisions_reserved honoured); all changed files within scope_paths.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- UNPIVOT type-homogeneity (build-breaking if any column were not FLOAT64): verified all 20 UNPIVOT IN-list
  columns in int_team_season__metrics.sql are produced by safe_divide(...) or CASE WHEN ... THEN NULL ELSE
  safe_divide(...) END — every branch is FLOAT64, so BigQuery UNPIVOT's equal-type requirement is satisfied;
  no CI type-mismatch. Passthrough columns (team_sk, season_sk, league_sk, league_code, season_api_year)
  confirmed present in the source; the macro is fully deleted with no live .sql caller; no AL09 self-alias.
- season_games_played >= 3 applied once + team_count correctness: the filter lives only in the long-form
  `season` CTE; neither the engine nor the mart re-applies it, so the population entering count(metric_value)
  (the rank-of-N denominator) is identical to the prior macro-driven UNION ALL. UNPIVOT EXCLUDE NULLS matches
  the prior explicit null filter; the retained defensive `where metric_value is not null` cannot change counts.
  Engine aggregates (count/avg/approx_quantiles group by league/season/metric) and the mart rank() window are
  byte-for-byte the same logic — numbers do not change.

## escalations
(none)
