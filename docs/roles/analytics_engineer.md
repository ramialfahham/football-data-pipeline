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

1. **Generic staging, unified raw tables (the zero-file rule).** All competitions share six unified raw tables discriminated by a `league_code` column; staging models are generic — one per entity, never per competition. Adding a league is one registry entry and zero model files; `league_code` flows through every layer as a column. There is NO per-competition staging and NO UNION-per-league loop (that architecture was retired; CI enforces).
2. **Tests are not optional.** Every new model needs grain tests. Every new metric needs a consistency test (rate = sum/count, ratio = num/denom) and, for ratios, the same-window rule: numerator and denominator computed over the same game set (coverage counts).
3. **Deduplication lives in base, not staging.** Staging is raw cleanup only. Base applies the first business logic (dedup, entity alignment). Materialisation is a LAYER decision set once in `dbt_project.yml` — currently `2_base: +materialized: table` (#547) — and a base model must never override it per model.
4. **Singular tests for pipeline health.** Stale fixtures, metric arithmetic, completeness — these are singular dbt tests, not schema tests, and they run in CI.
5. **Document the grain.** Every model description must state its grain. If you can't state the grain, the model isn't ready.
6. **Seeds and project config are code.** A seed row or `dbt_project.yml` change can alter mart behavior with zero SQL in the diff — it gets the same review, documentation and tests as a model change. The `metric_catalogue` seed is the single source of metric definitions (CPO-gated).
7. **The consumption layer computes nothing.** Everything downstream of the marts (export scripts, site code) may select, group, rename, format — never derive. See `dbt_project/docs/layering.md` §Consumption layer.

---

## Layer responsibilities (non-negotiable)

| Layer | Allowed | Not allowed |
|-------|---------|-------------|
| `1_staging` | Renaming, casting, unnesting, flattening — generic models reading the unified raw tables | Business logic, deduplication, per-competition models |
| `2_base` | Deduplication, entity alignment, first business logic (`2_base: +materialized: table`) | Metric calculation, joins to dims, per-competition ref() loops, any per-model materialized= |
| `3_core` | Surrogate keys, fact/dim grain enforcement, clean joins | `stg_*` refs, raw JSON parsing, competition-specific logic |
| `4_intermediate` | Complex transforms, feature engineering, window builders | Consumption-level formatting, refs to marts |
| `5_marts` | Denormalised, consumer-ready, competition-agnostic | Raw column exposure, untested metrics, hardcoded competitions |
| consumption (export/site) | Select, filter, group, rename, format, serialize | ANY computation: metric math, windows, ranking, affiliation, identity, taxonomy |

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
