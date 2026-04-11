# dbt Layering Rules

This document defines what is allowed in each dbt layer for this project.

## Layer Cheat Sheet

- `1_staging`: source-near cleanup only (renaming, typing, light normalization). No cross-source unions/joins.
- `2_base`: source-agnostic canonicalization (unions/alignment/entity resolution/technical keys).
- `3_core`: stable business entities and relationships reused across use cases.
- `4_intermediate`: heavier transformations and feature engineering.
- `5_marts`: consumer-ready outputs for app/BI/monitoring.

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

Purpose: technical consolidation and canonical shaping.

Allowed:
- Unions across staging models (for example all seasons for one league).
- Canonical column alignment across similar entities.
- Deterministic technical keys (for example `match_id`).
- Structural tests (for example `unique`, stronger `not_null`).

Not allowed:
- Heavy business KPIs or model-specific product logic.

## 3_core

Purpose: reusable business entities and relationship logic.

Allowed:
- Stable entities and semantic relationships.
- Shared business definitions used by multiple downstream consumers.

Not allowed:
- App-specific presentation logic.

## 4_intermediate

Purpose: complex transformations and feature engineering.

Allowed:
- Multi-step transforms.
- Window logic and derived feature sets for modeling.
- Expensive computations that should not be repeated in marts.

## 5_marts

Purpose: consumer-ready outputs.

Allowed:
- API/BI-ready tables.
- Clear naming and documentation for downstream use.
- Final aggregation or projection for product use cases.

## Testing Guidance by Layer

- `1_staging`: light data sanity checks close to source.
- `2_base`: key integrity and canonical-shape assertions.
- `3_core` and `4_intermediate`: relationship and business-rule tests.
- `5_marts`: consumer-contract and metric-consistency tests.

## Continuity: API-Football (free tier → paid plan)

When you add `2_base` and below, keep **plan and season** as **configuration**, not as magic numbers inside SQL.

- **Single season source for dbt:** define a dbt **variable** (for example `apif_season_year`) in `dbt_project.yml` or pass `--vars` in CI, sourced from the same convention as ingestion (`API_FOOTBALL_SEASON`). Downstream models should **reference the var** (or columns already present on staging/base such as `season_year` extracted from the payload) instead of hardcoding `2024` for “free tier”.
- **Stable grain and keys:** use API-stable identifiers (`fixture_id`, `team_id`, `player_id`, `league` id) as primary join keys. Paid vs free only changes **how many seasons and competitions** you load, not the shape of those keys.
- **Normalize envelope quirks in `2_base` only:** today staging exposes both full API envelopes (`fixtures`, `injuries`) and ingestion-wrapped arrays (`players`, `lineups`). Base is the right place to **one shape per entity** (for example one row per fixture, one row per player-team-season block) so `3_core` does not branch on “which raw layout”.
- **Sparse endpoints:** lineups and some injury rows are legitimately empty before kickoff or outside coverage. Prefer **conditional or relationship tests**, not blanket `not_null` on columns that the API documents as optional.
- **Promotion path:** when you upgrade, change **ingestion env** (`API_FOOTBALL_SEASON`, widen or drop season clamp envs) and **dbt vars / target** to the live season. If staging column contracts stay the same, **rebuild** downstream; avoid renaming marts columns unless you version or document a breaking change.

Together, this keeps the graph **ref()-stable** while the only operational change is “which season’s raw snapshots you load,” which is exactly what a paid plan unlocks.
