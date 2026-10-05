# dbt Layering Rules

This document defines what is allowed in each dbt layer for this project.

## BigQuery layout (datasets = schemas)

In BigQuery, a **dataset** is the unit that other databases often call a **schema**. This repo uses **one dataset per medallion layer** (same names as in `dbt_project.yml`):

| Dataset | What lives there |
|---------|------------------|
| **`raw`** | 1:1 ingestion from Python (unified `RAW_APIF_*` tables, e.g. `RAW_APIF_FIXTURES_NEXT`, shared across all competitions and discriminated by a `league_code STRING` column — there are no per-competition raw tables). dbt **sources** point here (`sources.yml` → `schema: raw`). Created by the `ingestion.api_football` package (entrypoint `python -m ingestion.api_football.main`); dataset id overridable with **`API_FOOTBALL_BIGQUERY_DATASET`**. |
| **`staging`** | `1_staging` dbt models: light cleanup on top of `raw`. |
| **`base`** | `2_base` models: **preparation for core**—entity resolution and first logical transformations (for example aligning how teams and fixtures are represented across sources). |
| **`core`** | `3_core` models: **system of record**—canonical **dimension** and **fact** tables. |
| **`intermediate`** | `4_intermediate` models: **preparation for marts**—complex logic, calculations, and cross-table joins that would be too heavy in a final delivery model. |
| **`marts`** | `5_marts` models: **consumption layer**—flattened, optimized shapes for application performance and for analytical exploration. |

dbt’s profile field **`dataset`** (`profiles.yml` / `profiles.example.yml`) is the **fallback** dataset for any model **without** a `+schema` (the base models + seeds). Configured layer models take their dataset from [`macros/generate_schema_name.sql`](../macros/generate_schema_name.sql), which prefixes the name by dbt target — see **Environment isolation** below.

**Ingestion vs dbt:** Python loads **`project.raw.*`**. dbt builds **`project.staging.*`**, **`project.base.*`**, etc. Same GCP **project**, different datasets.

### Environment isolation (prod / CI / dev)

`generate_schema_name` prefixes the layer datasets by the **dbt target name**, so each environment writes its own copy and can never clobber another:

| Target | Written by | Layer datasets | base + seeds (profile `dataset`) |
|--------|-----------|----------------|----------------------------------|
| `prod` | `dbt-scheduled` (nightly), `ci-data-build` main-push, `pages-match-preview` | `marts`, `core`, `staging`, `intermediate` (**bare**) | `dbt_analytics` |
| `ci_mr<IID>` | `data:build:mr`, **one target per merge request** (slim + `--defer` to prod) | `ci_mr114_marts`, `ci_mr114_core`, … | `ci_mr114` |
| `dev`  | local `dbt build` | `dev_marts`, `dev_core`, … | `dev_scratch` |

`prod` is the **only** target that writes the bare datasets the site export (`scripts/export_*.py`) reads — every other target is auto-prefixed, so a merge-request build or a local run cannot overwrite production. MR builds in CI stay fast by rebuilding only changed models (`state:modified+`) and **deferring** unchanged upstreams to prod. Snapshots are not yet target-aware (none exist today; see the note in `dbt_project.yml`).

⚠ **The CI target is PER MERGE REQUEST; there is no shared `ci` target** (#92, 2026-08-27). It used to be one `ci` target writing `ci_marts` / `ci_analytics` for every branch, and that shared workspace became a real defect the moment the singular tests started reading it instead of prod: a merge request that rebuilt nothing read tables another branch had built, and went red on three tests for reasons that had nothing to do with it. `.gitlab-ci.yml` now derives `DBT_CI_TARGET=ci_mr${CI_MERGE_REQUEST_IID}` and writes both the profile's output name and its `dataset:` from it, so `generate_schema_name`'s existing target-name prefix isolates the layer datasets and the profile `dataset:` isolates the base models and seeds. **The macro is unchanged.** These datasets are never expired or deleted; a full set is ~6 GB (~12¢/month).

⚠ **The two dbt invocations in `data:build:mr` differ by one flag ON PURPOSE.** `dbt build` runs `--defer --favor-state`; `dbt test` runs `--defer` alone. `--favor-state` resolves a `ref()` to the deferred prod relation even when the current run just built that model — right for a BUILD (its upstreams must come from prod), wrong for a TEST (it discarded the merge request's own models and pointed the whole singular suite at production). Both the asymmetry and the per-MR naming are pinned in `tests/test_ci_data_job_invariants.py`.

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

## Cross-layer consumption rule

From `2_base` upward, a model may `ref()` any model in the **same layer or any upstream layer**. The preferred path is always the nearest appropriate upstream layer — same-layer or skip-layer consumption should be deliberate, with the reason clear from the model's purpose.

`1_staging` is the only layer that is strictly isolated: staging models may only read from raw `source()` calls, never `ref()` another dbt model.

`scripts/check_layer_contract.py` (CI-enforced) checks:
- `staging` — no `ref()` calls; purity rules (no `group by`, `distinct`, cross joins, wrong `partition by`)
- `base` — cannot `ref()` `dim_*`, `fct_*`, `int_*`, or `mart_*`
- `core` — cannot `ref()` `stg_*` (must go through base) or `mart_*`
- `intermediate` — cannot `ref()` `mart_*`
- every layer — no model sets its own materialisation, except `incremental` on a `3_core` fact (§Materialisation)

## Materialisation

Set once per layer in `dbt_project/dbt_project.yml`. A model never sets its own, with the one
exception below; `scripts/check_layer_contract.py` enforces this on every layer.

| Layer | Config line |
|---|---|
| `1_staging` | `1_staging: +materialized: table` |
| `2_base` | `2_base: +materialized: table` |
| `3_core` | `3_core: +materialized: table` |
| `4_intermediate` | `4_intermediate: +materialized: table` |
| `5_marts` | `5_marts: +materialized: table` |

- **Tables, not views.** BigQuery bills every read of a view as a full re-run of everything beneath
  it, at least 10 MB for each table it reads. Every model has tests and readers, so a view is paid
  for many times a night and a table once. A view that ranks also ranks again on every read, so
  two readers of the same build can see different orders.
- **The one exception: `incremental` on a `3_core` fact whose source delivers only a per-run
  delta** (the latest fixtures), because a full rebuild from that source would lose the history. A
  fact whose source holds the full history stays a table rebuilt in full every night:
  `fct_fixture`, `fct_fixture_event`, `fct_standings`,
  `fct_team_market_value_snapshot`, and `fct_fixture_player_stats` and `fct_fixture_team_stats`,
  whose base keeps every match's latest line, so a change to the cleaning reaches every match.
- No ephemeral models.

## Goals

- Keep model responsibilities clear.
- Make tests easier to place and reason about.
- Reduce accidental logic duplication across layers.

## 1_staging

Purpose: source-near cleanup with minimal transformation.

Materialisation: see §Materialisation.

A staging model does exactly two things, in this order:

1. **Snapshot selection.** The unified raw tables are append-only logs. How a model selects
   from that log depends on how its loader lands data:
   - **Complete-snapshot tables (the default).** Each run appends one *complete* snapshot row
     per `league_code` (all configured seasons merged into that row). Select the newest
     snapshot per `league_code` —
     `qualify row_number() over (partition by league_code order by ingested_at desc) = 1`. It
     is *snapshot selection across an append log*, not entity deduplication: it picks one raw
     row before flattening and collapses nothing within it.
   - **Incremental-accumulation tables.** A few loaders are *skip-if-already-ingested*: to stay
     within the API budget they fetch only entities not already landed, so each run's snapshot
     holds only that run's NEW entities, never a complete set (e.g. the per-player
     `/players/profiles` and `/players/teams` pulls). These models must read **all** snapshots
     (`select * from {{ source(...) }}` with no latest-snapshot qualify) — selecting the latest
     snapshot would silently drop entities landed on earlier runs. It is still a faithful
     flatten with no entity dedup; assembling current-per-entity is a base concern. A table is
     incremental-accumulation **iff** its loader is skip-if-present, and that must be stated in
     the model header and its `stg_apif__generic.yml` entry. (Recognized 2026-06-15 by CPO
     ruling; the first such tables are `RAW_APIF_PLAYER_PROFILES` / `RAW_APIF_PLAYER_TEAMS`.)
   - **Sub-league keyed tables.** A few raw tables are keyed at a grain *below* `league_code` —
     one row per fixture (`RAW_APIF_FIXTURE_DETAILS`) or per `(team, season)`
     (`RAW_APIF_PLAYERS`) — because the loader fetches per entity, skip-if-already-ingested. They
     hold **many keys per `league_code`** and, since 2026-08-17, **several versions per key**: the
     loader appends a retry alongside the payload it used to replace, so raw carries every version
     the provider gave us (CPO ruling, "raw keeps both versions"). Like incremental-accumulation
     tables these read **all** rows (`select * from {{ source(...) }}` with no latest-snapshot
     qualify) — a `partition by league_code` qualify would keep one fixture or one team-season per
     league and drop every other. It is still a faithful flatten with no entity dedup. The staging
     grain therefore carries `raw_ingested_at`, and choosing between versions is base's job:
     newest-per-entity-key, which is exactly where the layer contract puts that decision.
     State the read-all rationale in the model header and its `stg_apif__generic.yml` entry.
     (Grain recognized 2026-06-22 by CPO ruling, #539. The delete-on-retry that used to bound
     these tables was REMOVED 2026-08-17 — see `docs/data_contract.md`, "Raw appends and never
     deletes", for what it destroyed and why it is not coming back.)
2. **Faithful 1:1 flatten.** Unnest that snapshot's JSON payload into one typed row per
   entity, rename to snake_case, and cast. Every entity present in the selected snapshot
   must appear exactly once in the output — nothing merged, aggregated, or dropped
   (beyond discarding rows missing a grain key, e.g. a null id or date).

The line that matters: **snapshot selection partitions on `league_code` alone and acts on
the raw row; entity deduplication partitions on entity keys (player_id, fixture_id,
team_id, …) after flattening — and that belongs in base, never staging.**

Allowed:
- Latest-snapshot selection per `league_code` (partition on `league_code` only) for
  complete-snapshot tables; reading **all** rows (no qualify) for incremental-accumulation
  (skip-if-present) and sub-`league_code`-keyed tables — see step 1.
- Source-to-model mapping (one staging model per raw source table).
- Column renaming to consistent naming conventions (snake_case).
- Safe type casting and lightweight normalization.
- JSON extraction, unnesting, and flattening (including `cross join`/`left join unnest(...)`
  to explode arrays) needed to expose one regular typed table per raw source.
- Dropping rows that are missing a grain key (null id/date) — this is cleanup, not dedup.
- Model-level tests per [`engineering_standards.md`](engineering_standards.md) §3: document the **grain** in the model `description`; `not_null` on required fields; `unique` or `dbt_utils.unique_combination_of_columns` on grain keys; constrained `accepted_values` where useful. (Full testing policy lives in that doc—do not under-test staging relative to §3.)

Not allowed:
- **Entity-grain deduplication** — any `qualify`/`row_number()`/`distinct` that collapses rows
  on entity keys. Dedup is a base concern (`2_base`), if it happens at all.
- **Aggregation or pivoting** — `group by`, `sum`/`max`/`any_value` to reshape many rows into
  one (e.g. a statistics pivot). Reshaping is business logic; do it in base.
- Unions across leagues/competitions/sources.
- Cross-domain joins (joining two different entities). Lateral `unnest(...)` of the model's
  own payload is flattening, not a cross-domain join, and is allowed.
- Helper/bridge/derived staging models that are not direct source mappings.
- Business rules and feature engineering.

**Hard contract (Path B):** staging is **generic** — one `stg_apif__<entity>.sql` per unified
raw table (`RAW_APIF_<entity>`), discriminated by the `league_code` column. There are **no**
per-competition staging models. `models/1_staging/api_football/` must contain **no**
per-competition subdirectory and no `stg_apif__<league>_*` files; `scripts/check_layer_contract.py`
fails CI if one appears. Adding a league requires **zero** staging files (see `CLAUDE.md`).

## 2_base

Purpose: **preparation for the core layer.** Base turns staging into a coherent cross-source view: **entity resolution**, shared identifiers, and **first logical transformations** so the warehouse agrees on what a team, fixture, or other entity *is* before facts and dimensions are finalized.

Allowed:
- Unions and alignment across staging models where the same real-world entity appears in more than one place.
- Standardized keys and attributes that downstream layers can rely on without re-negotiating source quirks.
- Structural tests (for example `unique`, stronger `not_null`) on grains and keys you define here.

Not allowed:
- Declaring the authoritative business **fact** or **dimension** system of record (that belongs in **core**).
- Presentation or delivery logic aimed at a specific app or report.
- `ref()`-ing a core / intermediate / mart model. Base sits below them in the DAG and may only read `stg_*` or other `base_*` models. *(CI-enforced by `scripts/check_layer_contract.py`.)*
- Setting materialisation on a model (§Materialisation). *(CI-enforced by `check_layer_contract.py`.)*

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
   - ⚠ `dim_country` and `dim_region` (#69) were a RECORDED EXCEPTION to this condition too, not just to the "attribute masquerading as entity" bullet below: they shipped with **zero** consumers on 2026-08-17. `dim_country` gained real ones the same day — #69 step 5's four `relationships` tests (`core.yml`). **`dim_region` did not**: `mart_competition_index` (#62 step 3, MR !65) reads `confederations`, the seed `dim_region` itself publishes from, not `dim_region` — the two are siblings off the same seed, and `dim_region` is still, today, a genuine zero-consumer exception. Same ruling, same authority — `escalations.log`, 2026-08-17, `feat/69-country-region-dims`. Noted in both places deliberately: a reader who checks only this rule would otherwise find the contradiction with nothing explaining it.
3. **Conformance.** The vocabulary is one the whole warehouse agrees on. If two sources disagree on what the same entity is, resolve the conflict in `2_base` before the dimension crystallizes in `3_core`.

Patterns that look like dimensions but are not:

- **Degenerate dimension.** A natural key with no independent attributes (e.g. a round name, an invoice number): keep the key on the fact; do not build a table.
- **Closed enum.** A small, stable vocabulary (fixture status, event type, card colour): enforce with `accepted_values` on the fact; a dim adds maintenance without adding information.
- **Attribute masquerading as entity.** Country, nationality, position, language: keep as attributes until a consumer needs rollups or hierarchies (e.g. continent, confederation, position group). Promote to a dim when the rollup logic appears, not before.
  - ⚠ **COUNTRY IS AN EXPLICIT, RECORDED EXCEPTION TO THIS BULLET — not a case of it being satisfied.** `dim_country` and `dim_region` (#69, 2026-08-17) shipped with **no reader at all**. `dim_country` gained real ones the same day, once #69 step 5 landed — the four FK `relationships` tests in `core.yml` (`league_country`, `team_country`, `player_birth_country`, `coach_birth_country`, each `to: ref('dim_country')`). **`dim_region` still has none**: `mart_competition_index` (#62 step 3, MR !65) resolves its region sub-line from `confederations`, the seed `dim_region.sql` itself is published from — a sibling consumer, not a consumer of `dim_region` — so `grep -rn "ref('dim_region')" dbt_project/models/` returns zero hits and the exception below is still live for that dim alone. The rollup this bullet names as the trigger — confederation on the country — is STILL what `dim_country` leaves out either way: it carries no confederation column, because there is no source for one at the country grain (the registry gives a confederation per COMPETITION, not per country). The reason the exception was granted is a different problem from the one this bullet guards: country was free text in four dims, spelled up to three ways for the same country, with no list of what "valid" looked like, and that absence is what made a `single_country` boolean look like a solution. CPO 2026-08-16: *"You don't mix up countries and continents or regions in one column and add a flag 'single country'. That's really bad modeling."* The ruling is in `escalations.log` (2026-08-17, `feat/69-country-region-dims`). **The bullet still stands for everything else** — position, language and nationality are still attributes, and the next promotion still needs either the rollup or its own ruling.
- **Entity requiring cross-source resolution.** If consolidating the entity requires reconciling identifiers across sources (e.g. venue from `/teams` vs `/fixtures`), that work lives in `2_base`; `3_core` receives the already-conformed version.

**Relationship (mapping) dimensions.** A `dim_…_mapping` may also be a *conformed relationship table* resolving a many-to-many association between existing dimensions — e.g. `dim_player_team_season_mapping`, recording which players were rostered to which team in which season. This is the one sanctioned exception to qualification rule #1 (Entity) and to the degenerate-dimension exclusion: the "thing" it represents is the association itself, so it legitimately carries only the participating keys (plus lineage), with no independent descriptive attributes. It must still satisfy **Reuse** and **Conformance**, and — like every core table — have a single **tested, unique grain key** (its surrogate over the full grain). That uniquely-keyed grain is precisely what qualifies it as a system-of-record object; on that key it is a clean one-row-per-key lookup. The `_mapping` suffix marks its grain and role: each row is an *association across dimensions*, not a single entity, so joining on one participating key (e.g. `player_sk`) resolves a many-to-many relationship and returns many rows by design.

Canonical dimension inventory for this project:

| Dim | Grain | Source staging model | Notes |
|-----|-------|----------------------|-------|
| `dim_date` | day | generated via `dbt_utils.date_spine` | Global; not league-scoped. |
| `dim_league` | league_api_id | `base_apif__league_entity` | One row per configured league; surrogate key is the API integer directly. |
| `dim_competition_season` | (league_api_id, season_api_year) | `base_apif__competition_seasons` | Carries API coverage flags that drive downstream conditional logic. |
| `dim_team` | team_api_id | `base_apif__teams_global` | Pure global entity (identity only); surrogate key is the API integer directly. Carries no competition/season affiliation — membership lives in `dim_team_competition_season_mapping`, per-match facts in `fct_fixture`. |
| `dim_player` | player_api_id | `base_apif__players` | Pure global entity (identity only); surrogate key is the API integer directly. Not league-scoped and carries no team/season affiliation — roster membership lives in `dim_player_team_season_mapping`, appearances in the facts. |
| `dim_player_team_season_mapping` | (player_sk, team_sk, season_api_year, league_code) | `base_apif__player_team_season` | Relationship (mapping) dim, not an entity: rostered player↔team↔season membership incl. never-played squad members. Keys only, no descriptive attributes; many rows per player. |
| `dim_team_competition_season_mapping` | (team_sk, league_code, season_api_year) | `base_apif__fixtures_next` | Relationship (mapping) dim: team↔competition↔season membership derived from fixtures (finished + scheduled), so a team is a member from the moment its schedule is published. Keys only; many rows per team. Sourced from fixtures (not the `/teams` roster) because a team always plays the competitions it enters — no never-played gap like a player's, so no roster source is needed. |
| `dim_coach` | coach_api_id | `base_apif__coaches` | Pure global entity (identity / bio only); surrogate key is the API integer directly. No league_code or affiliation — managerial history lives in `dim_coach_team_mapping`. |
| `dim_coach_team_mapping` | (coach_sk, team_api_id, start_date) | `base_apif__coach_career` | Relationship (mapping) dim: coach↔team managerial stints (clubs managed) with start/end dates. `team_sk` is a SOFT link — the career team set (youth / reserve / untracked clubs) exceeds `dim_team`, so no strict FK; the provider `team_api_id` + `team_name` are kept. Keys + dates; many rows per coach. |

All league-scoped dimensions carry `league_code` in both natural and surrogate keys so additional leagues can be added without collisions.

### Fact qualification rules

A table earns `fct_` status only when **all three** conditions hold:

1. **Event or measurement.** It captures something that happened at a point in time (a match, a transfer, a card) or the state of a measure at a point in time (standings on a given day). A reference list with no time dimension does not qualify.
2. **Dimensional context.** It joins to one or more dims via foreign keys and/or carries degenerate dim columns that pin the event/measurement to a team, player, season, and date.
3. **Measures or atomic grain.** It carries additive/semi-additive measures (goals, minutes, shots, points), or it is the atomic grain of a state that downstream models aggregate. Wide denormalized shapes designed for a single consumer belong in `5_marts`, not `3_core`.

Patterns that look like facts but are not:

- **Derived metric table.** Top scorers, top assists, top yellow cards from API-Football are rankings over per-player events and statistics. They are **derived** from `fct_fixture_player_stats` and `fct_fixture_event` and live in `4_intermediate` or `5_marts` once a consumer needs them. Ingesting them as facts in `3_core` would duplicate the underlying measures.
- **Degenerate fact.** Rounds are only labels attached to fixtures, with no measures of their own. Keep them as a degenerate attribute on `fct_fixture` (`round_name`); a separate `fct_round` adds no information.
- **Consumer-specific denormalization.** A wide per-team season summary is a **mart**, not a core fact, even when it carries measures — facts in `3_core` stay at their atomic grain so multiple marts can aggregate them differently.
- **Deferred fact.** `fct_prediction` and `fct_fixture_lineup` each pass the three-condition test in principle but are deferred until a mart consumer actually queries them; ingesting to `3_core` without a consumer adds maintenance without value.

Canonical fact inventory for this project:

| Fact | Grain | Source staging model(s) | Notes |
|------|-------|-------------------------|-------|
| `fct_fixture` | `fixture_sk` (= `fixture_api_id`) | `base_apif__fixtures_next` | Match header; status, round, and venue travel as degenerate attributes. Half-time / extra-time / penalty splits deferred. |
| `fct_standings` | `(season_sk, team_sk, group_name)` | `base_apif__standings` (from generic `stg_apif__standings`) | Current league position per team-season; raw payload is replaced wholesale per season on each ingest. |
| `fct_fixture_team_stats` | `(fixture_sk, team_sk)` | `base_apif__fixture_statistics` | `statistics_lines_json` pivoted to named columns; dedup in base layer. |
| `fct_fixture_player_stats` | `(fixture_sk, team_sk, player_sk)` | `base_apif__fixture_players` | `player_statistics_json[0]` flattened into measures. |
| `fct_fixture_event` | `event_sk` hashed over full staging grain | `base_apif__fixture_events` | `assist_player_name` stays as a degenerate attribute (no id in source). |
| `fct_team_market_value_snapshot` | `(team_sk, as_of_date, source_code)` | seed `wc_team_market_value_snapshot` | Seed-loaded WC national-team squad market-value snapshots (EUR). WC-scoped — no `league_code`. |

Most facts propagate `league_code` so they are safe to union across future leagues
(the seed-sourced `fct_team_market_value_snapshot` is the WC-only exception).

Materialisation, including which facts are `incremental`: see §Materialisation.

### Snapshots

The project does not currently use dbt snapshots. The product surfaces only the current state of every entity, so adding SCD2 history without a downstream consumer is over-engineering — and the `unique_key` design is easy to get wrong (a previous `snap_apif_d1_standings` snapshot included `group_description` in the key, which leaked stale zone rows into `fct_standings`). If a future feature genuinely needs SCD2 history, configure `unique_key` from the entity's stable identity only and put changing attributes in `check_cols`.

## 4_intermediate

Purpose: **preparation for the marts layer.** Intermediate is where **complex logic**, multi-step **calculations**, and **cross-table joins** live when they would make **marts** models too heavy, repetitive, or hard to test.

Allowed:
- Reusable blocks of logic shared by several mart models.
- Windowed or multi-stage calculations that are easier to reason about in dedicated models than inside a final delivery table.
- Joins and reshaping that are still internal to the warehouse graph, not final consumption shape.

Not allowed:
- End-user-facing table design (naming, flattening, and optimization for a specific consumer are **marts** concerns).
- **`ref('mart_*')`.** Intermediate feeds marts, not the reverse. CI runs `scripts/check_layer_contract.py` to fail on any `4_intermediate/**/*.sql` that references a mart.

**Naming in this repo:** `int_matchday__*` holds matchday preview / form / fixture-denorm spine; `int_team_season__*` holds team-season rollups helpers (e.g. deduped standings for marts); `int_pipeline__*` holds ingestion-monitoring or warehouse-operation helpers (for example raw load-time spread).

## 5_marts

Purpose: **consumption layer.** Marts expose **flattened**, **query-efficient** datasets intended for **applications** (low-latency, stable contracts) and for **analytical work** (exploration, exports, BI) without requiring consumers to navigate the full internal graph.

Allowed:
- Models shaped for known consumers: clear grains, documented columns, and tests that match how the table will be used.
- Denormalization and pre-aggregation where they improve latency or usability at the point of use.

Not allowed:
- Re-defining core business truth that should remain centralized in **core** (marts should select and present, not fork definitions silently).

### Mart conventions

- Every mart carries `league_code` as a column so multi-league slicing is a filter, not a schema change. When a second league is onboarded, marts do not need to be rewritten.
- Materialisation: see §Materialisation.

Canonical mart inventory (exhaustive) for this project:

| Mart | Grain | Notes |
|------|-------|-------|
| `mart_team_season` | (team_sk, season_sk) | Per-team-per-season rollup over finished matches; latest rank, form, and standings group label joined from `fct_standings`. |
| `mart_leaderboards` | (player_sk, season_sk, metric_key) | LONG per-board player leaderboards, the thirteen boards of the competition page's Rankings tab (11 count + 2 rate, the rate boards behind a minutes and position floor); generalises the retired `mart_top_scorers`. Composes `int_player_season__metrics`; top-10 per board, DENSE_RANK ties share, every board most first. |
| `mart_team_leaderboards` | (team_sk, season_sk, metric_key) | LONG per-board team leaderboards — the team mirror of `mart_leaderboards` (GAP-29). Twelve boards, the Rankings tab's, each ranked in the direction the `metric_catalogue` seed gives its metric and serving it as `rank_order` (the two "against" rates ascending; the two card totals most first by ruling). Composes `int_team_season__metrics` (UNPIVOT, not a union-all loop — one shared rule, unlike the player rate boards) + the catalogue seed + `dim_team`; no games floor; top-10 per board, DENSE_RANK ties share; a zero ranks only on an ascending board. Rank partitions `(league_code, season_api_year, metric_key)` — per league by ruling, so the ranking never crosses competitions. |
| `mart_next_matchday` | fixture_sk | Every competition's next matchday: each upcoming fixture (NS/TBD, dated on or after the build day) in the round of that competition's earliest upcoming fixture. The Home hero reads it whole; nothing is capped or ordered in it. `is_match_that_matters` flags, per competition, the fixture whose two teams have the lowest sum of table positions. |
| `mart_matchday_insights` | fixture_sk (per `league_code`) | MVP domestic upcoming matchday + form; filter by `league_code` at export/UI. BL1 play-offs: `mart_matchday_insights_bl1_relegation`. WC: `mart_matchday_insights_wc`. |
| `mart_team_season_insights` | (league_code, team_sk) | MVP latest season per league; slice by `league_code` at export/UI. |
| `mart_standings` | (league_code, season_api_year, group_name, team_sk) | The league's official standings row, the provider's except where corrected to the league's figures (rank, points, W/D/L, goals scored and conceded, goal difference, form) plus `table_kind`, the section's kind (league / group / conference / split_round / ranking) resolved from its name through the `standings_table_kinds` seed. |
| `mart_competition_season_summary` | (league_code, season_api_year) | The season's headline tallies over finished matches: matches, goals, goals per match, home/away/draw split, the biggest-margin and most-goals fixtures, the longest unbeaten and winless runs with their holders. Composes `int_legs__team_match`; results tallied at competition grain, not catalogue metrics. |
| `mart_team_market_value` | team_sk | Team squad market value; currently WC-scoped (see #418 to generalize). |
| `mart_team_profile` | (team_sk, season_sk) | v2 team profile: full-season metrics, YoY deltas, streaks. |
| `mart_player_profile` | (player_sk, season_sk) | v2 player profile rollup. |
| `mart_player_match_log` | (player_sk, fixture_sk) | Per-player per-fixture match log. |
| `mart_team_momentum` | (upcoming_fixture_sk, team_sk) | W1 last-5 momentum aggregate (team). |
| `mart_player_momentum` | (upcoming_fixture_sk, team_sk, player_sk) | W1 momentum aggregate (player). |
| `mart_team_momentum_window` | (upcoming_fixture_sk, team_sk, played_fixture_sk) | W1 momentum-window drill-down legs (team). |
| `mart_team_season_record` | (upcoming_fixture_sk, team_sk) | W2 season-record aggregate (team). |
| `mart_player_season_record` | (upcoming_fixture_sk, team_sk, player_sk) | W2 season-record aggregate (player). |
| `mart_team_fixture_stats` | (fixture_sk, team_sk) | Per-fixture team stat lines. |
| `mart_player_fixture_stats` | (fixture_sk, team_sk, player_sk) | Per-fixture player stat lines. |
| `mart_fixture_standing_context` | (fixture_sk, team_sk) | Pre-fixture standings / rank context. |
| `mart_head_to_head` | (team_sk, opponent_team_sk) | Head-to-head history per team pair. |
| `mart_roster` | (team_sk, league_code, season_api_year, player_sk) | Identity-only club squad list from `dim_player_team_season_mapping` ⋈ `dim_player`; club-scoped via `competition_types`. No per-club stat columns of its own; the Squad tab's per-player stats come from `mart_player_career` (#480), joined onto the roster at the export. |
| `mart_team_competition_benchmarks` | (team_sk, season_sk, metric_key) | LONG team-vs-league benchmark over the 22 team season metrics; value · league median/mean/p25/p75 · rank (k of N) · vs-median. Composes `int_team_competition_benchmark_metrics_long` (shared per-team long form) + `int_team_competition_benchmarks` (the league distribution). Direction-agnostic (positional). |
| `mart_player_competition_benchmarks` | (player_sk, season_sk, position_group, metric_key) | LONG player-vs-positional-peers benchmark; in-position per-90/rate value · peer median/mean/p25/p75 · rank (k of N) + percentile · vs-median. Composes `int_player_competition_benchmark_metrics_long` (shared per-player long form: the metric set, position eligibility and who enters) + `int_player_competition_benchmarks` (the positional distribution). Direction-agnostic (positional). |
| `mart_player_career` | (player_sk, team_sk, season_sk) | Player Career log: one row per player × club × competition-season (appearances/goals/assists) + player/club identity + `entity_type`. Composes `int_player_club_season__metrics` (the per-club atoms base, #480 §8.3); a mid-season transfer = two rows; national-entity rows = national appearances in covered competitions (NOT true caps); `national_appearances_total` denormalised per player. |

## Consumption layer (export scripts, site builds) — NOT a dbt layer, bound by this contract

> CPO ruling (2026-06-11): "All the logic and transformation is done in dbt. We could
> consume from the metrics using any frontend tooling. Transformations, logic must
> never happen in the frontend."

Everything downstream of the marts — `scripts/export_site_data.py`, the legacy
`export_pages_data.py`, `site/`, `site_v2/` — is **frontend**. The marts are the
product's data API: complete, finished, consumable by any tool.

Allowed in the frontend:
- Select, filter, group, paginate; drop join/plumbing keys; rename for the payload.
- Formatting and serialization: locale number/date rendering, JSON file layout,
  sitemaps, cache headers.
- Routing mechanics.

**Never allowed in the frontend** (each of these has produced or nearly produced a
drift bug):
- Metric math, window selection, result/perspective computation.
- **ALL ranking and ordering. The page renders the order it is served.** CPO ruling 2026-09-09
  (`escalations.log`), in his words *"yes, that's the rule"* to that sentence. This is not new — it
  is the section's own test at the foot of this list ("would this value deserve a DQ test, or need
  to be byte-identical across two frontends?") applied without exception. It is spelled out because
  the wording it replaces — "ordering that encodes a business rule" — let every case be argued
  individually, and that argument was had once per block. There is no
  ordering that does not encode one: even a tie-break decides who a reader sees, so it is the
  warehouse's. Leaderboard ranks live in marts; `mart_leaderboards.rank` and its tie-broken sibling
  `league_leader_order` are the pattern.
  What it costs, put to the CPO before he ruled and accepted: a block needing a new ordering waits
  on a mart column. What it buys: no per-block argument, and two frontends cannot disagree about
  who is top.
  ⚠ **A SHIPPED FILE IS NOT A PRECEDENT FOR BREAKING THIS.** The rule was nearly weakened by citing
  `site_v2/src/lib/competitionOrder.mjs`, a frontend module that sorts on five keys, as evidence
  that ordering belongs on the page. CPO: *"I don't even know what it is. Definitely no
  authoritative document for business logic."* Under this rule that module is a violation awaiting
  its own task. Authority is this document, the working agreement, and `escalations.log` — never
  the existence of code, and never the justification an agent wrote in its own header.
- Entity derivation (e.g. player→team affiliation) or identity generation (slugs are
  published URL identity — they must come from the warehouse so every frontend links
  identically).
- Taxonomy mappings (competition groupings etc. — those are seeds/registry fields).

The test: **would this value deserve a DQ test, or need to be byte-identical across
two frontends? Then it belongs in dbt.** If no mart serves a value a page needs,
that is a data gap — register it and ship the mart first; never bridge it in Python.
Edit-time guardrail: `dbt_layer_gate.py` injects this contract when an export/site
file is edited.

## Testing Guidance by Layer

- `1_staging`: light data sanity checks close to source.
- `2_base`: key integrity and canonical-shape assertions.
- `3_core` and `4_intermediate`: relationship and business-rule tests on shared logic.
- `5_marts`: consumer-contract tests (required columns, grains, allowed values) and checks that outputs stay aligned with upstream **core** definitions.
