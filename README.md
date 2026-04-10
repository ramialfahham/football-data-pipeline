# football-data-pipeline
Modular ELT pipeline to aggregate and model football data from multiple sources using Python, BigQuery, and dbt.

## dbt (local setup)

The dbt project lives in `dbt_project/`. For CI/CD readiness, `profiles.yml` is **not** committed.

- Copy `dbt_project/profiles.example.yml` to your local dbt profiles directory as `profiles.yml`
  - Default location on Windows: `%USERPROFILE%\.dbt\profiles.yml`
  - Or set `DBT_PROFILES_DIR` to point to a folder containing `profiles.yml`

Run from the repo root (with the root `venv` activated):

```powershell
dbt --version
dbt deps --project-dir .\dbt_project
dbt debug --project-dir .\dbt_project
dbt parse --project-dir .\dbt_project
```

## Data Quality (tests)

Recommended local workflow:

```powershell
# Staging-only checks (fast, catches raw load issues early)
dbt build --project-dir .\dbt_project --selector staging

# Base-layer checks (unions/alignment + keys)
dbt build --project-dir .\dbt_project --selector base

# Full suite (all models + all tests)
dbt build --project-dir .\dbt_project
```

## dbt Layer Contract

This project follows a strict layer contract so transformations stay predictable and testable.

- `1_staging`: raw cleanup only (renaming, typing, light normalization). No unions across leagues/sources.
- `2_base`: unions and alignment into canonical structures. Technical keys and structural quality checks.
- `3_core`: reusable business entities and clean relationship logic.
- `4_intermediate`: heavier transformations and feature engineering.
- `5_marts`: app/BI-ready outputs for consumption.

Detailed rules: `dbt_project/docs/layering.md`.
Engineering standards: `dbt_project/docs/engineering_standards.md`.
Ingestion operations standards: `docs/ingestion_standards.md`.
API-Football MVP scope: `docs/api_football_mvp_scope.md`.
Data dictionary and definition confidence: `docs/data_dictionary.md`.
