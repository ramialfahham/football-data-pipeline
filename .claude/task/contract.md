# Task contract — remove the team_benchmark_metrics macro (COMPOSE: one shared long-form model)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> CPO-directed (2026-06-27): "Do it" — remove the team benchmark-list macro. Applies the §1.3 macro
> standard merged in #592 (a shared list belongs in a model, not a macro). TEAM only; player reserved.

objective: >
  Replace the `team_benchmark_metrics()` Jinja macro — a 20-branch UNION ALL unpivot driver duplicated in
  the benchmark engine and the benchmark mart — with ONE shared long-form model both read (COMPOSE).
  Numbers must not change (the benchmark mart feeds the site once #391 ships); equivalence is by
  construction and CI's benchmark DQ tests are the gate (dbt CLI is broken locally).

refs: >
  CPO "Do it" 2026-06-27. Applies engineering_standards.md §1.3 (merged #592). TEAM only — the player
  macro (`player_benchmark_metrics`, encodes position eligibility) and the dormant scaffolding macros are
  NOT touched. Follows the COMPOSE pattern (compute once, downstream reads).

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/macros/team_benchmark_metrics.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/layering.md

impact_map: >
  CHANGE: replace the team_benchmark_metrics() macro (20-branch UNION ALL unpivot driver, used in two
  models) with one shared long-form model both consumers read (COMPOSE), per §1.3.

  WRITERS / DAG (evidence: git grep ref()):
  - NEW int_team_competition_benchmark_metrics_long (view): unpivots the 20 benchmark metrics from
    int_team_season__metrics (season_games_played >= 3) to per-(team_sk, season_sk, metric_key) long form
    via BigQuery UNPIVOT.
  - int_team_competition_benchmarks (table, engine): now selects + group by league_code, season_api_year,
    metric_key over the long-form (was its own UNION ALL unpivot). Output grain + columns unchanged.
  - mart_team_competition_benchmarks (view): now ranks the long-form per team + joins the engine (was its
    own UNION ALL unpivot). Output grain + columns unchanged.
  - DELETE macros/team_benchmark_metrics.sql.

  DOWNSTREAM / BLAST RADIUS:
  - mart_team_competition_benchmarks is a LEAF: git grep ref('mart_team_competition_benchmarks') = 0; no
    scripts/export_* or site* consumes it (not yet wired to the paused #391 site). No live export/number
    is reachable from this change.
  - int_team_competition_benchmarks is referenced only by the mart (one ref).
  - NUMBERS: zero change by construction. The long-form yields exactly the per-(team,season,metric) values
    the macro's UNION ALL produced (same 20 columns, all FLOAT64 via safe_divide/CASE — verified — so
    UNPIVOT type-aligns; same >=3 filter). Engine avg/quantiles/count over those values grouped by
    league/season/metric = the prior aggregates (the extra team-grain keys do not affect the grouping).
    The mart rank over the same values = the prior ranks. UNPIVOT default EXCLUDE NULLS == the prior
    `where metric_value is not null` filters (kept defensively in both consumers).

  CI / TESTS: ci-data-build builds dbt_analytics; the dbt DAG orders long-form -> engine -> mart. Existing
  benchmark DQ tests (unique_combination + accepted_values on metric_key + not_null) re-run; a new
  unique_combination + accepted_values(20 metrics) on the long-form verifies the unpivot's metric set.

  LAYER RULES: long-form (intermediate) refs int_team_season__metrics (intermediate) — OK; mart composes
  intermediates — OK; no intermediate refs a mart — OK.

decisions_taken: >
  Number-preserving internal refactor. New model name int_team_competition_benchmark_metrics_long follows
  the existing int_team_competition_benchmark* convention; materialized as a view (cost-neutral — same
  unpivot execution count as today; the mart stays a view, the engine stays a table). No metric, product,
  or output-contract change; the mart's grain/columns/materialization are identical.

decisions_reserved:
  - The player benchmark macro (player_benchmark_metrics) — encodes position eligibility; separate, careful PR.
  - Whether the long-form should be a table (vs view) if the benchmark later becomes query-hot — defer until
    a consumer exists (#391 paused).

done_when:
  - team_benchmark_metrics.sql is deleted; no model references it (mcp__dbt__parse clean).
  - The engine + mart read int_team_competition_benchmark_metrics_long; their output grain/columns are
    unchanged; the new model has a description + >=1 test (unique_combination + accepted_values).
  - Required reviewers (scope-auditor, analytics-engineer-reviewer) PASS with >=2 risks each; review.md
    diff_sha256 binds the staged diff; CI green (incl. the benchmark DQ tests). The CPO merges.

amendments: (none)
