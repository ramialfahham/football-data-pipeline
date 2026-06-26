# Metric layer

> How the platform keeps its metrics consistent — the dbt-idiomatic way. Short by design.

## Where each thing lives (read this first)

**The `dbt_project/seeds/metric_catalogue.csv` seed is the single source of truth for every metric
definition** — `metric_id`, formula (`numerator` / `denominator`), `description`, display `format`,
and the display taxonomy (`metric_group`, `importance_tier`, `group_display_order`, `direction`,
`interpretation`). No prose document defines a metric; docs *reference* the seed, never redefine it.

| You need… | Go to |
|---|---|
| a metric's definition / formula / units | **the `metric_catalogue.csv` seed** (the SSoT) |
| how a metric is **displayed** (group, tier, order, row patterns) | `docs/wireframes/metrics_display.md` |
| which past matches form a window + how it's labelled | `docs/metrics_context_model.md` |
| how the layer stays consistent (compute-once + the drift guard) | this document (below) |

## The three parts

1. **Each metric is computed in exactly one place.** The canonical per-grain model
   (`int_player_season__metrics` for player-season; `int_team_season__metrics` for team-season)
   computes it once. Consolidating onto one model (#480 for player; #500 for team) is what prevents
   *implementation* drift — the same metric computed three different ways. (The *definition* lives in
   the seed, above; the model is where it is computed.)
2. **The catalogue is the registry + glossary.** `dbt_project/seeds/metric_catalogue.csv` is the single list
   of every metric: `metric_id`, label (i18n key), definition, formula (numerator / denominator), display
   format, and grouping. The UI glossary (`metrics.json`) is built from it. It documents; it does not compute.
3. **Tests verify and guard.**
   - **No-drift guard** — `tests/assert_no_uncatalogued_season_metric.sql`: every metric-bearing column in a
     canonical season model must be a `metric_catalogue` row, so a computed metric can't be added without
     registering it (CI fails otherwise). Keys, coverage counts, `*_sum_season` intermediates and the
     playing-time facts are excluded; the `_season` suffix and the `goals_saves`→`saves` quirk are normalised
     (pending #500's name alignment).
   - **Correctness** — standard dbt tests on the models: ratios in 0–1 (per-match rates and
     finishing-efficiency are uncapped), not-null + relationships on keys, unique on the grain.

## What it is NOT

There is no bespoke "metric engine": no binding-map, no `metric_kind` taxonomy, no test that re-derives a
metric from the raw legs to cross-check the model. The model computes it once; the catalogue documents it;
the drift test stops uncatalogued metrics creeping in. That is the whole mechanism.

## Adding a metric

1. Add the computation to the canonical model (one place).
2. Add the `metric_catalogue` row (id, label, definition, format, group).
3. The drift test passes once both exist; add a 0–1 range test if it is a ratio.

## Non-metrics

`league_rank` (a standings lookup) and `points_won` (a window-header tally) are catalogue rows for the
glossary but are not computed metrics; they are not in the canonical season models, so the drift guard does
not involve them. Playing-time facts (appearances, minutes, starts, subs) are dimensions, not metrics, and
are excluded from the guard.

## Scope / follow-ups

- Phase 1 covers the two **season** grains. The form-window grains are a later phase (same pattern).
- Model / column naming consistency + the team-season model consolidation: **#500**.
