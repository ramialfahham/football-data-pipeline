# Data Dictionary and Definition Confidence

This document defines confidence levels for data definitions and records how column meanings are confirmed.

## Confidence Levels

- `verified`: field meaning is explicitly confirmed by official source documentation.
- `inferred`: field meaning is derived from payload structure/naming and still needs source-doc confirmation.

## Verified Source Documents

- API-Sports Football v3 documentation: https://www.api-football.com/documentation-v3

## Current Status by Source

- `api_football`: top-level payload naming is currently `inferred` until each field is cross-checked with official docs.

## Update Process

When a new source field is confirmed with official docs:

1. Add/update mapping in this document.
2. Update model/column descriptions in dbt YAML.
3. Add or tighten quality tests where applicable.
