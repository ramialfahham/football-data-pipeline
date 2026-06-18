# Task contract — feat: metric layer (Phase 1) — catalogue completeness + drift guard

> The metric layer, done the dbt-idiomatic way. The season MODELS are the single source of truth for each
> metric (already so — #480 for player-season; team-season consolidation tracked in #500). This task just
> (a) makes the catalogue COMPLETE — every metric the two season models already compute is registered —
> and (b) adds ONE drift guard: a test that fails if a model computes a metric not in the catalogue, plus
> standard range tests. NO bespoke conformance engine, NO binding-map, NO metric_kind column — those were
> over-built (re-deriving every metric to check the model) and have been reverted; they bought nothing over
> #480's single source + a drift test. CPO-directed, 2026-06-18.

objective: >
  (1) Add the 4 catalogue rows for metrics the season models ALREADY compute but that are not registered:
  shot_share + points_capture (int_team_season__full_season_metrics), shots_total + goals_conceded
  (int_player_season__metrics). (2) Add a drift-guard test: for each canonical season model, every
  metric-bearing column — excluding keys, coverage counts, *_sum_season intermediates, and the playing-time
  facts (appearances/starts/subs/minutes) — maps to a metric_catalogue metric_id; fails on any uncatalogued
  metric. Normalisation: strip the team `_season` suffix; map the one `goals_saves`->`saves` quirk (NOT a
  binding-map — two rules). (3) Range tests (0-1) on the ratio metrics. (4) docs/metric_layer.md describing
  the layer: model = single source; catalogue = registry/docs; drift test = guard; standard dbt tests =
  correctness. NO model SQL changes.

refs: >
  This conversation 2026-06-18. Metric layer = model-as-single-source (#480) + catalogue-as-registry + a
  drift guard, NOT a recompute engine (reverted after the CPO flagged it as over-built). Naming + team-season
  model consolidation = #500. Season-grain completeness beyond the 4 orphans (e.g. clean_sheets at season
  grain) is a separate concern, not this task.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/macros/
  - dbt_project/tests/
  - docs/metric_layer.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO 2026-06-18: build the metric layer the dbt-idiomatic way — model = single source (#480/#500),
  catalogue = registry/docs, ONE drift-guard test (no uncatalogued metric), standard dbt tests for
  correctness. The bespoke conformance engine (binding-map seed, metric_kind, context flag, recompute-from-
  legs test) was over-built and is reverted. league_rank/points_won stay plain catalogue rows (they are the
  UI glossary's source too). The drift test handles the goals_saves<->saves quirk + the _season suffix via
  small normalisation, not a binding-map.

decisions_reserved:
  - No recompute/conformance engine; no binding-map; no metric_kind column; no context flag.
  - No model SQL changes — the models already compute these metrics; this task only catalogues + tests.
  - Season-grain completeness beyond the 4 orphans (clean_sheets / per-match T-I-B / dribbles% at season
    grain) is a SEPARATE task, not bundled here.
  - Naming consistency + team-season model consolidation = #500 (not here).

done_when:
  - metric_catalogue has the 4 orphan rows (shot_share, points_capture, shots_total, goals_conceded).
  - The drift test passes now and WOULD FAIL if a season model gained an uncatalogued metric column.
  - The ratio metrics have 0-1 range tests.
  - docs/metric_layer.md documents the (simple) mechanism.
  - validate-local green; ci-data-build green on the PR.
  - reviewer (per .claude/review_routing.json): analytics-engineer-reviewer + football-analytics-expert-reviewer
    (metric_catalogue.csv) + scope-auditor PASS (>=2 named risks each); no FAIL; no ESCALATE.
  - Branch feat/metric-layer-phase1; PR opened (CPO merges).

amendments: (none)
