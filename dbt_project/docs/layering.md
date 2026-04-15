# dbt Layering Rules

This document defines what is allowed in each dbt layer for this project.

## BigQuery layout (datasets = schemas)

In BigQuery, a **dataset** is the unit that other databases often call a **schema**. This repo uses **one dataset per medallion layer** (same names as in `dbt_project.yml`):

| Dataset | What lives there |
|---------|------------------|
| **`raw`** | 1:1 ingestion from Python (`RAW_<league>_APIF_*` tables, e.g. `RAW_D1_APIF_*`). dbt **sources** point here (`sources.yml` → `schema: raw`). Created by the `ingestion.api_football` package (entrypoint `python -m ingestion.api_football.main`); dataset id overridable with **`API_FOOTBALL_BIGQUERY_DATASET`**. |
| **`staging`** | `1_staging` dbt models (views by default): light cleanup on top of `raw`. |
| **`base`** | `2_base` models (views): **preparation for core**—entity resolution and first logical transformations (for example aligning how teams and fixtures are represented across sources). |
| **`core`** | `3_core` models (tables): **system of record**—canonical **dimension** and **fact** tables. |
| **`intermediate`** | `4_intermediate` models (tables): **preparation for marts**—complex logic, calculations, and cross-table joins that would be too heavy in a final delivery model. |
| **`marts`** | `5_marts` models (tables): **consumption layer**—flattened, optimized shapes for application performance and for analytical exploration. |

dbt’s profile field **`dataset`** (`profiles.yml` / `profiles.example.yml`) is the **fallback** dataset for any model **without** a `+schema`; with [`macros/generate_schema_name.sql`](../macros/generate_schema_name.sql), configured layer models use **only** the custom name (`staging`, `base`, …), not `dbt_scratch_staging`.

**Ingestion vs dbt:** Python loads **`project.raw.*`**. dbt builds **`project.staging.*`**, **`project.base.*`**, etc. Same GCP **project**, different datasets.

The dbt variable **`raw_schema`** (default **`raw`** in `dbt_project.yml`) must match the BigQuery dataset id used by ingestion (`API_FOOTBALL_BIGQUERY_DATASET`). Override either in sync, for example:

`dbt build --project-dir .\dbt_project --vars '{raw_schema: raw_dev}'`

### Adding another landing source (recommended pattern)

1. **Tables:** keep using the shared **`raw`** dataset; add tables with a **clear prefix** (e.g. `RAW_OPTA_*`, `RAW_STATS_BOMB_*`) so sources never collide.
2. **Ingestion:** isolate loaders under `ingestion/<source>/` (same pattern as `ingestion/api_football/`).
3. **dbt:** add `models/1_staging/<source>/sources.yml` pointing at `schema: "{{ var('raw_schema') }}"` and staging models named `stg_<source>__<entity>` (see `engineering_standards.md`).
4. **Do not** nest datasets as `raw/api_football` — BigQuery has no subdatasets; use **prefixes** or, if IAM requires it, a **separate** dataset `raw_<source>` and a second dbt var (only when needed).

## Layer Cheat Sheet

- `1_staging`: source-near cleanup only (renaming, typing, light normalization). No cross-source unions/joins.
- `2_base`: preparation for **core**—entity resolution and first logical standardization across sources.
- `3_core`: **system of record**—canonical dimensions and facts.
- `4_intermediate`: preparation for **marts**—complex logic, derived fields, and joins that should not live in consumption models.
- `5_marts`: **consumption layer**—delivery-oriented tables for apps and analysis.

## Goals

- Keep model responsibilities clear.
- Make tests easier to place and reason about.
- Reduce accidental logic duplication across layers.

## 1_staging

Purpose: source-near cleanup with minimal transformation.

Allowed:
- Source-to-model mapping (often 1:1 by table/season/competition).
- Column renaming to consistent naming conventions (snake_case).
- Safe type casting and lightweight normalization.
- Source-level and light model-level quality tests (for example `not_null`, `accepted_values`).

Not allowed:
- Unions across leagues/competitions/sources.
- Business rules and feature engineering.
- Cross-domain joins.

## 2_base

Purpose: **preparation for the core layer.** Base turns staging into a coherent cross-source view: **entity resolution**, shared identifiers, and **first logical transformations** so the warehouse agrees on what a team, fixture, or other entity *is* before facts and dimensions are finalized.

Allowed:
- Unions and alignment across staging models where the same real-world entity appears in more than one place.
- Standardized keys and attributes that downstream layers can rely on without re-negotiating source quirks.
- Structural tests (for example `unique`, stronger `not_null`) on grains and keys you define here.

Not allowed:
- Declaring the authoritative business **fact** or **dimension** system of record (that belongs in **core**).
- Presentation or delivery logic aimed at a specific app or report.

## 3_core

Purpose: **system of record** for the modeled domain. Core holds the canonical **dimension** and **fact** tables: stable grains, vetted definitions, and relationships that other layers treat as the single source of truth.

Allowed:
- Dimensions and facts that multiple use cases are expected to share.
- Relationship logic and conformed attributes that marts and intermediate models should reuse rather than re-derive.

Not allowed:
- Wide, consumer-specific projections or performance-oriented denormalization (those belong in **marts**, with support from **intermediate** where needed).

## 4_intermediate

Purpose: **preparation for the marts layer.** Intermediate is where **complex logic**, multi-step **calculations**, and **cross-table joins** live when they would make **marts** models too heavy, repetitive, or hard to test.

Allowed:
- Reusable blocks of logic shared by several mart models.
- Windowed or multi-stage calculations that are easier to reason about in dedicated models than inside a final delivery table.
- Joins and reshaping that are still internal to the warehouse graph, not final consumption shape.

Not allowed:
- End-user-facing table design (naming, flattening, and optimization for a specific consumer are **marts** concerns).

## 5_marts

Purpose: **consumption layer.** Marts expose **flattened**, **query-efficient** datasets intended for **applications** (low-latency, stable contracts) and for **analytical work** (exploration, exports, BI) without requiring consumers to navigate the full internal graph.

Allowed:
- Models shaped for known consumers: clear grains, documented columns, and tests that match how the table will be used.
- Denormalization and pre-aggregation where they improve latency or usability at the point of use.

Not allowed:
- Re-defining core business truth that should remain centralized in **core** (marts should select and present, not fork definitions silently).

## Testing Guidance by Layer

- `1_staging`: light data sanity checks close to source.
- `2_base`: key integrity and canonical-shape assertions.
- `3_core` and `4_intermediate`: relationship and business-rule tests on shared logic.
- `5_marts`: consumer-contract tests (required columns, grains, allowed values) and checks that outputs stay aligned with upstream **core** definitions.
