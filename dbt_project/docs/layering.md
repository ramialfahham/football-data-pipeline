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
