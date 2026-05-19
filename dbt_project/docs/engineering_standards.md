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
  - intermediate: `int_<domain>__<purpose>` — use **`int_matchday__*`** for matchday preview / form / fixture denorm spine, **`int_team_season__*`** for per-team-season preparation (e.g. standings dedupe), **`int_pipeline__*`** for ingestion or warehouse-operation helpers (for example raw load-time spread). Intermediate must not `ref()` any `mart_*` model.
  - marts: `mart_<consumer_or_domain>__<purpose>`
- Columns use lowercase snake_case.
- Boolean columns start with `is_` or `has_`.
- Timestamp columns end with `_at`, dates end with `_date`.

## 1.1) SQL Structure and Readability

- Every model starts with explicit import CTEs for each `ref()` / `source()` relation before transformation logic.
- Prefer named CTE chains over inline subqueries. Avoid `from ( ... )` when the same logic can be expressed as a named CTE.
- Keep each CTE single-purpose (import, explode/flatten, dedupe/rank, final projection) and use stable, descriptive CTE names.
- For BigQuery array expansion, prefer explicit `cross join unnest(...)` style over implicit comma joins where practical.

## 1.2) Code Comments (Python and SQL)

Comments exist to convey **why**, not **what**. Well-named identifiers, CTEs, and functions already describe what the code does. A comment is warranted when the reader would otherwise be left wondering why a decision was made, what constraint is being respected, or what non-obvious behaviour to expect.

**Write a comment when:**
- A design decision has a non-obvious reason (e.g. why a coverage flag is overridden for finished fixtures)
- An invariant must hold for downstream code to be correct
- A workaround exists for a specific API quirk or external constraint
- The behaviour would surprise a competent reader unfamiliar with this domain

**Do not write a comment when:**
- The code already reads clearly from its identifiers and structure
- You would only be paraphrasing what the next line does
- The context is already captured in the PR description or a linked ticket

**Module / file level:** Every Python module and every dbt model should open with a one-sentence docstring or comment stating its purpose and its place in the pipeline (e.g. "Fetches qualifier fixtures per supporting league and merges into a single BQ payload."). This is the first thing a new engineer reads.

**Function / CTE level:** A short docstring on non-trivial functions. For SQL, a one-line comment before each CTE when its purpose is not obvious from its name.

**Inline:** Reserve for genuinely surprising logic. One line is almost always enough. Avoid multi-line comment blocks.

**Standard applied consistently across Python and SQL.** A senior engineer reading any file in this repo should be able to orient themselves within 30 seconds.

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

## 9) Data Freshness and SLAs

- Define expected refresh cadence per source (for example daily pre-match refresh).
- Add source freshness checks when reliable load timestamps are available.
- Fail pipelines on stale critical sources once freshness is implemented.

## 10) Security and Secrets

- Never commit API keys, service account files, or secret env values.
- Use environment variables for external API authentication.
- Keep service roles least-privileged where possible.

## 11) GitHub Pages export contract

- **Source of league list:** `vars.active_competition_league_codes` in `dbt_project.yml`, domestic subset only (exclude `WC` and `WCQ*`).
- **Warehouse:** One `mart_matchday_insights` for all domestic leagues (`league_code` on every row); `mart_matchday_insights_bl1_relegation` only for BL1 play-offs; `mart_matchday_insights_wc` for WC fixture previews; `mart_wc_pre_tournament_insights` for optional team browse only; one `mart_team_season_insights` table for all leagues. Do not add per-league filter views or codegen copies in `5_marts`.
- **Play-off windows:** Exclude play-off `round_name` values from the unified mart via dbt vars (`bl1_relegation_round_names`, `bl2_playoff_round_names`, `l1_relegation_round_names`). BL1 relegation legs use the dedicated mart + export fallback; BL2 promotion legs appear on the BL1 relegation path only. Policy and CPO checklist: [`docs/playoff_window_policy.md`](../../docs/playoff_window_policy.md).
- **Exporter:** `scripts/export_pages_data.py` queries unified marts with `WHERE league_code = @code`, writes `artifacts/data/{league_lower}/…`, and `artifacts/pages_export_manifest.json`. BL1 matchday falls back to the relegation mart when the domestic slice is empty. Each domestic entry includes `matchday_row_count`, `team_season_row_count`, and `matchday_source_mart`. WC is a separate `wc` object on the manifest (`matchday_path`, `matchday_row_count`, `matchday_source_mart`, `wc_pre_tournament_path` for secondary browse) sourced from `mart_matchday_insights_wc` at `data/wc/matchday_insights.json`.
- **UI routing vs labeling:** Landing phase is derived from manifest row counts (`matchday_row_count > 0` → fixture-list; else recap). `matchday_source_mart` drives relegation copy only (e.g. suffix when the source mart name contains `relegation`). Never hardcode per-league phase overrides in the UI for play-offs.
- **Site layout:** `_site/data/{league}/` plus manifest at `_site/pages_export_manifest.json`; `match-preview/matchday_insights.json` is optional BL1 compat copy until the UI reads the manifest.
