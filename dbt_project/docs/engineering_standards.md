# dbt Engineering Standards

This document defines practical standards for analytics engineering in this project.
Use it together with [`layering.md`](layering.md) (BigQuery dataset layout and layer rules).

## 0) Warehouse layout

- **Raw landing** lives in the BigQuery dataset named by dbt **`raw_schema`** (default `raw`). Ingestion must use the **same** dataset id (`API_FOOTBALL_BIGQUERY_DATASET` for API-Football).
- **Additional vendors:** prefer new `RAW_<VENDOR>_…` tables in the **same** `raw` dataset and a new folder `models/1_staging/<vendor>/` unless IAM forces a separate `raw_<vendor>` dataset.

## 1) Naming Conventions

- Model names use lowercase snake_case.
- Prefix by layer intent:
  - staging: `stg_<source>__<entity>`
  - base: `base_<domain>__<entity>`
  - core: `core_<entity>`
  - intermediate: `int_<domain>__<purpose>`
  - marts: `mart_<consumer_or_domain>__<purpose>`
- Columns use lowercase snake_case.
- Boolean columns start with `is_` or `has_`.
- Timestamp columns end with `_at`, dates end with `_date`.
- Competition identity above staging must use `league_code` only. Provider ids/codes stay in ingestion and staging.

## 1.1) SQL Structure and Readability

- Every model starts with explicit import CTEs for each `ref()` / `source()` relation before transformation logic.
- Prefer named CTE chains over inline subqueries. Avoid `from ( ... )` when the same logic can be expressed as a named CTE.
- Keep each CTE single-purpose (import, explode/flatten, dedupe/rank, final projection) and use stable, descriptive CTE names.
- For BigQuery array expansion, prefer explicit `cross join unnest(...)` style over implicit comma joins where practical.

## 1.2) SQL Performance Gate (enforced)

- In `2_base` / `3_core` / `4_intermediate` / `5_marts`, do not use `select *` unless a reviewer approves an explicit exception (`sql-quality: allow-select-star` comment).
- For simple dedupe/top-1 where rank is not reused, prefer `qualify row_number() over (...) = 1` over `where rn = 1` with an extra rank alias.
- Keep expensive expressions centralized (single CTE) when reused in multiple downstream projections.
- CI enforces these rules on changed SQL files via `scripts/check_sql_quality.py`.

## 2) Documentation Policy

- Every model must have a `description`.
- Business-facing columns in `core`, `intermediate`, and `marts` must have `description`.
- Every source table must have a short source description in `sources.yml`.
- Keep descriptions factual and concise; avoid implementation details.

## 3) Testing Policy

- `staging`: document the **grain** (one row per what) in the model `description`. Then:
  - `not_null` on columns required for that row to be valid (ids, dates, join keys).
  - `unique` or `dbt_utils.unique_combination_of_columns` on the column(s) that define the grain, so dupes and bad merges fail early.
  - Constrained `accepted_values` (and other light tests) where they add signal.
  - Do **not** repeat the **same** uniqueness assertion downstream unless the **grain changes** (avoid redundant tests on the same keys in `base` / later layers).
- `base`: structural integrity when unions or reshaping apply—stronger `not_null`, key quality, `relationships`, and `unique` / composite tests where the grain is new or combined across sources (not a copy of staging’s uniqueness if nothing changed).
- `core`/`intermediate`: relationship and business-rule tests.
- `marts`: consumer-contract tests (required columns, accepted value ranges, metric consistency).
- Every new model requires at least one meaningful test.

## 4) Model Contracts and Metadata

- Use model contracts for stable `marts` outputs once schemas stabilize.
- Add `meta` fields for ownership:
  - `owner`
  - `domain`
  - `criticality` (`low|medium|high`)
- Use `tags` consistently (for example `daily`, `pre_match`, `api`).

## 5) Performance Standards (BigQuery)

- Prefer views for lightweight `staging`.
- Use tables for heavy transforms in `intermediate` and high-query `marts`.
- For large tables, apply partitioning and clustering (typically on date/time and league/team keys).
- Avoid repeated expensive expressions across layers; centralize once in `intermediate` if reused.

## 6) Environment and Promotion

- Keep `profiles.yml` out of git (already required in this repo).
- Use separate datasets/targets for `dev` and `prod`.
- Validate in `dev` before promotion.
- Do not introduce breaking mart schema changes without a migration plan.

## 7) CI/CD Minimum Gate

Every PR should pass:

1. `dbt deps --project-dir .\dbt_project`
2. `dbt parse --project-dir .\dbt_project`
3. `dbt build --project-dir .\dbt_project --selector staging`
4. `dbt build --project-dir .\dbt_project --selector base`

Before release to prod:

5. `dbt build --project-dir .\dbt_project`

## 8) Change Management

- Prefer additive changes over destructive renames/drops.
- If output schema must change, document:
  - what changes
  - why it changes
  - migration impact for downstream consumers
- Keep marts stable as product/API contracts.

## 8.1) Product Visibility and Lifecycle

- App-facing marts must respect lifecycle-driven visibility windows (prelaunch/live/post-season), not hardcoded league literals.
- Ingestion status (`active`, `in_progress`, etc.) is operational metadata; app visibility is a separate product concern.
- Hide completed/off-season competitions from primary pre-match surfaces without deleting warehouse history.

## 8.2) International Tournament Metric Policy (WC26)

- Do not blend qualifier/international context with tournament-only performance into one composite metric.
- Keep separate outputs:
  - `recent_form_*` for international/qualifier context.
  - `tournament_form_*` for World Cup matches only.
- Expose tournament sample size fields and explicit null/fallback semantics when tournament sample is empty.

## 8.3) Localization (i18n) Contract

- Use stable identifiers and keys in marts; avoid embedding final localized copy in warehouse logic.
- Never use translated strings as join keys or filter predicates.
- Presentation layer (app) owns locale-specific rendering from stable data keys.

## 9) Data Freshness and SLAs

- Define expected refresh cadence per source (for example daily pre-match refresh).
- Add source freshness checks when reliable load timestamps are available.
- Fail pipelines on stale critical sources once freshness is implemented.

## 10) Security and Secrets

- Never commit API keys, service account files, or secret env values.
- Use environment variables for external API authentication.
- Keep service roles least-privileged where possible.
