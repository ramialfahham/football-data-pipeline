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
3. **dbt:** add `models/1_staging/<source>/sources.yml` pointing at `schema: "{{ var('raw_schema') }}"` and staging models named `stg_<source>__<entity>` (naming: [engineering_standards.md](engineering_standards.md) §1).
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
- Source-to-model mapping (strictly 1:1 by raw source table for this project).
- Column renaming to consistent naming conventions (snake_case).
- Safe type casting and lightweight normalization.
- JSON extraction, unnesting, and flattening needed to expose one regular typed table per raw source.
- Model-level tests per [`engineering_standards.md`](engineering_standards.md) §3: document the **grain** in the model `description`; `not_null` on required fields; `unique` or `dbt_utils.unique_combination_of_columns` on grain keys; constrained `accepted_values` where useful. (Full testing policy lives in that doc—do not under-test staging relative to §3.)

Not allowed:
- Unions across leagues/competitions/sources.
- Helper/bridge/derived staging models that are not direct source mappings.
- Business rules and feature engineering.
- Cross-domain joins.

**Hard contract:** `models/1_staging/api_football/` must contain exactly **13** `stg_apif__bl1_*.sql` files—one per `RAW_D1_APIF_*` source in [`sources.yml`](../models/1_staging/api_football/sources.yml). Adding a 14th helper model in staging is a contract violation and must fail CI.

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

### Dimension qualification rules

A table earns `dim_` status only when **all three** conditions hold:

1. **Entity.** It represents a real-world thing the business talks about by name (team, player, season, date, league). A lookup table for a closed enum does not qualify on its own.
2. **Reuse.** Its attributes are shared across more than one fact or mart. If an attribute set is consumed by exactly one consumer, denormalize it onto that consumer's fact or mart instead.
3. **Conformance.** The vocabulary is one the whole warehouse agrees on. If two sources disagree on what the same entity is, resolve the conflict in `2_base` before the dimension crystallizes in `3_core`.

Patterns that look like dimensions but are not:

- **Degenerate dimension.** A natural key with no independent attributes (e.g. a round name, an invoice number): keep the key on the fact; do not build a table.
- **Closed enum.** A small, stable vocabulary (fixture status, event type, card colour): enforce with `accepted_values` on the fact; a dim adds maintenance without adding information.
- **Attribute masquerading as entity.** Country, nationality, position, language: keep as attributes until a consumer needs rollups or hierarchies (e.g. continent, confederation, position group). Promote to a dim when the rollup logic appears, not before.
- **Entity requiring cross-source resolution.** If consolidating the entity requires reconciling identifiers across sources (e.g. venue from `/teams` vs `/fixtures`), that work lives in `2_base`; `3_core` receives the already-conformed version.

Canonical dimension inventory for this project:

| Dim | Grain | Source staging model | Notes |
|-----|-------|----------------------|-------|
| `dim_date` | day | generated via `dbt_utils.date_spine` | Global; not league-scoped. |
| `dim_league` | (league_code, league_api_id) | `stg_apif__bl1_leagues` | One row per configured league. |
| `dim_season` | (league_code, season_api_year) | `stg_apif__bl1_leagues` (seasons_json) | Carries API coverage flags that drive downstream conditional logic. |
| `dim_team` | (league_code, team_api_id) | `stg_apif__bl1_teams` | Deduplicated to latest-season snapshot; home-venue attributes denormalized until a first-class `dim_venue` is justified. |
| `dim_player` | (league_code, player_api_id) | `stg_apif__bl1_players` | Deduplicated to latest (team, season); `last_known_team_api_id` is a snapshot attribute, not a join key. |

All league-scoped dimensions carry `league_code` in both natural and surrogate keys so additional leagues can be added without collisions.

### Fact qualification rules

A table earns `fct_` status only when **all three** conditions hold:

1. **Event or measurement.** It captures something that happened at a point in time (a match, a transfer, a card) or the state of a measure at a point in time (standings on a given day). A reference list with no time dimension does not qualify.
2. **Dimensional context.** It joins to one or more dims via foreign keys and/or carries degenerate dim columns that pin the event/measurement to a team, player, season, and date.
3. **Measures or atomic grain.** It carries additive/semi-additive measures (goals, minutes, shots, points), or it is the atomic grain of a state that downstream models aggregate. Wide denormalized shapes designed for a single consumer belong in `5_marts`, not `3_core`.

Patterns that look like facts but are not:

- **Derived metric table.** Top scorers, top assists, top yellow cards from API-Football are rankings over per-player events and statistics. They are **derived views** over `fct_fixture_player_stats` and `fct_fixture_event` and live in `4_intermediate` or `5_marts` once a consumer needs them. Ingesting them as facts in `3_core` would duplicate the underlying measures.
- **Degenerate fact.** Rounds are only labels attached to fixtures, with no measures of their own. Keep them as a degenerate attribute on `fct_fixture` (`round_name`); a separate `fct_round` adds no information.
- **Consumer-specific denormalization.** A wide per-team season summary is a **mart**, not a core fact, even when it carries measures — facts in `3_core` stay at their atomic grain so multiple marts can aggregate them differently.
- **Deferred fact.** `fct_injury`, `fct_prediction`, and `fct_fixture_lineup` each pass the three-condition test in principle but are deferred until a mart consumer actually queries them; ingesting to `3_core` without a consumer adds maintenance without value.

Canonical fact inventory for this project:

| Fact | Grain | Source staging model(s) | Notes |
|------|-------|-------------------------|-------|
| `fct_fixture` | `fixture_sk` (= `fixture_api_id`) | `stg_apif__bl1_fixtures_next` | Match header; status, round, and venue travel as degenerate attributes. Half-time / extra-time / penalty splits deferred. |
| `fct_standings` | `(season_sk, team_sk, group_description)` | `snap_apif_d1_standings` (from `stg_apif__bl1_standings`) | Current snapshot only; history is in the dbt snapshot table. |
| `fct_fixture_team_stats` | `(fixture_sk, team_sk)` | `stg_apif__bl1_fixture_statistics` | `statistics_lines_json` pivoted to named columns. |
| `fct_fixture_player_stats` | `(fixture_sk, team_sk, player_sk)` | `stg_apif__bl1_fixture_players` | `player_statistics_json[0]` flattened into measures. |
| `fct_fixture_event` | `event_sk` hashed over full staging grain | `stg_apif__bl1_fixture_events` | `assist_player_name` stays as a degenerate attribute (no id in source). |
| `fct_transfer` | `transfer_sk` hashed over (league, player, date, from, to, type) | `stg_apif__bl1_transfers` | `{from,to}_team_sk` nullable: transfers frequently touch teams outside the configured leagues. |

All facts propagate `league_code` so they are safe to union across future leagues.

### Snapshots

Some endpoints only return the current state (notably `/standings`). To preserve history without inflating fact grain, we use dbt's native `snapshots` feature:

- Snapshot files live in `dbt_project/snapshots/` and target the **`snapshots`** BigQuery dataset (configured via `dbt_project.yml`).
- Naming convention: `snap_<source>_<table>` (e.g. `snap_apif_d1_standings`).
- `strategy='check'` with `check_cols` on the measure columns; `dbt snapshot` is run as part of the daily pipeline before `dbt build`.
- Core facts (`fct_standings`) read the current version (`where dbt_valid_to is null`); historical queries read the snapshot directly.

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

### Mart conventions

- Every mart carries `league_code` as a column so multi-league slicing is a filter, not a schema change. When a second league is onboarded, marts do not need to be rewritten.
- Rollup marts (one row per business entity and grain) materialize as `table`; flat denormalized projections materialize as `view` unless a latency requirement forces a table.

Canonical mart inventory for this project:

| Mart | Grain | Materialization | Notes |
|------|-------|-----------------|-------|
| `mart_fixture_results` | fixture_sk | view | Flat fixture table with both teams, league, season, and kickoff-date denormalized; default consumer shape. |
| `mart_team_season` | (team_sk, season_sk) | table | Per-team-per-season rollup over finished matches; latest rank / form joined from `fct_standings`. |
| `mart_player_season` | (player_sk, season_sk) | table | Per-player-per-season rollup over finished matches; per-fixture team attribution stays in `fct_fixture_player_stats`. |
| `mart_top_scorers` | (player_sk, season_sk) | view | Top-25 ranking derived from `mart_player_season`; replaces the dropped `/players/topscorers` ingestion. |

## Testing Guidance by Layer

- `1_staging`: light data sanity checks close to source.
- `2_base`: key integrity and canonical-shape assertions.
- `3_core` and `4_intermediate`: relationship and business-rule tests on shared logic.
- `5_marts`: consumer-contract tests (required columns, grains, allowed values) and checks that outputs stay aligned with upstream **core** definitions.
