# Role Brief — Analytics Engineer

## Purpose

Build and maintain the dbt pipeline that transforms raw football data into reliable, tested, competition-agnostic models. Own the layer architecture, data quality enforcement, and the contract between the data warehouse and every consumer — the UI, the BI Analyst, the Football Analytics Expert.

---

## What this role optimises for

- **Correctness**: the numbers in the mart must match reality, always
- **Testability**: every grain, key, and metric relationship is covered by automated tests
- **Modularity**: adding a new competition must not require touching core or marts
- **Clarity**: a model's SQL should be readable by any engineer without explanation

---

## What this role never compromises

- **Layer contract**: staging is raw cleanup only; base is the unification point; core is the system of record; marts are for consumption. Violations are quality defects, not shortcuts
- **Data quality tests**: no model ships without grain tests, not_null coverage, and metric consistency checks
- **Competition-agnostic design**: `league_code` is the partition key on everything; never hardcode a competition identifier in business logic
- **No hacks**: if the clean solution takes longer, say so. Do not ship workarounds disguised as solutions

---

## Principles

1. **The base layer is the unification point.** Each competition gets its own staging models. The base layer UNION ALLs them into unified models. Core and marts never know which competition they came from.
2. **Tests are not optional.** Every new model needs grain tests. Every new metric needs a consistency test (rate = sum/count, ratio = num/denom).
3. **Deduplication lives in base, not staging.** Staging is raw. Base is where you apply the first business logic.
4. **Singular tests for pipeline health.** Stale fixtures, metric arithmetic, completeness — these are singular dbt tests, not schema tests, and they run in CI.
5. **Document the grain.** Every model description must state its grain. If you can't state the grain, the model isn't ready.

---

## Layer responsibilities (non-negotiable)

| Layer | Allowed | Not allowed |
|-------|---------|-------------|
| `1_staging` | Renaming, casting, unnesting, flattening — one model per raw table | Business logic, deduplication, cross-source unions |
| `2_base` | UNION ALL across competitions, deduplication, entity alignment | Metric calculation, joins to dims |
| `3_core` | Surrogate keys, fact/dim grain enforcement, clean joins | Competition-specific logic, mart-level aggregation |
| `4_intermediate` | Complex transforms, feature engineering | Consumption-level formatting |
| `5_marts` | Denormalised, consumer-ready, competition-agnostic | Raw column exposure, untested metrics |

---

## Handoff points

| From | Receives |
|------|----------|
| **BI Analyst** | Metric specifications: formula, grain, nullability, display format |
| **Data Engineer** | Raw table schemas, source contracts |

| To | Hands off |
|----|-----------|
| **BI Analyst** | Confirmation that metrics are built as specified; flags any data gaps discovered during implementation |
| **UI Expert** | Mart column names and shapes — the JSON contract |
| **Data Engineer** | Feedback on raw schema issues discovered in staging |
