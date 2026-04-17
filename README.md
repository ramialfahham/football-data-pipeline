# football-data-pipeline
Modular ELT pipeline to ingest and model football data from API-Football using Python, BigQuery, and dbt.

## BigQuery layout (datasets)

BigQuery uses **datasets** as the unit that other databases often call **schemas**. This repo uses **one dataset per medallion layer** in the same GCP project:

| Dataset | Role |
|---------|------|
| **`raw`** | 1:1 loads from Python (`RAW_*` tables). Default; override with `API_FOOTBALL_BIGQUERY_DATASET` (ingestion) and dbt **`raw_schema`** var (must match). |
| **`staging`** | dbt `1_staging` — light cleanup on top of `raw`. |
| **`base`** → **`marts`** | dbt `2_base` … `5_marts` per `dbt_project.yml`. |

dbt uses [`macros/generate_schema_name.sql`](dbt_project/macros/generate_schema_name.sql) so layer names map **directly** to dataset ids (not `dbt_scratch_staging`). The profile’s default **`dataset`** (`dbt_scratch` in `profiles.example.yml`) is only a fallback for nodes without `+schema`.

Details and multi-source conventions: [`dbt_project/docs/layering.md`](dbt_project/docs/layering.md).

**MVP:** ingestion and dbt **`1_staging`** are scoped to **German Bundesliga (D1)** only. Folders **`2_base`–`5_marts`** exist for the layer contract but contain no models yet (placeholders). Until you add models there, `dbt parse` / `dbt build` may warn that those folder configs apply to no resources; that is expected.

## dbt (local setup)

The dbt project lives in `dbt_project/`. For CI/CD readiness, `profiles.yml` is **not** committed.

- Copy `dbt_project/profiles.example.yml` to your local dbt profiles directory as `profiles.yml`
  - Default location on Windows: `%USERPROFILE%\.dbt\profiles.yml`
  - Or set `DBT_PROFILES_DIR` to point to a folder containing `profiles.yml`

**Local Python (single convention):** the repo uses **`.venv/`** at the root (gitignored). Set it up once, then use it for ingestion, dbt, and SQLFluff:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run dbt from the repo root with **`.venv`** activated:

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

# Base layer only (no models until you add them under models/2_base)
dbt build --project-dir .\dbt_project --selector base

# Base + core + intermediate + marts (when those folders contain models)
dbt build --project-dir .\dbt_project --selector downstream

# Full suite (staging + downstream + tests)
dbt build --project-dir .\dbt_project

# Optional: point dbt at a non-default raw dataset (must match ingestion target)
# dbt build --project-dir .\dbt_project --vars "{ raw_schema: raw_dev }"
```

For expectations by layer (grain, `not_null`, `unique`, avoiding duplicate tests downstream), see [engineering_standards.md §3 (Testing policy)](dbt_project/docs/engineering_standards.md).

## dbt Layer Contract

This project follows a strict layer contract so transformations stay predictable and testable.

- `1_staging`: raw cleanup only (renaming, typing, light normalization). No cross-source unions/joins (details in [layering.md §1_staging](dbt_project/docs/layering.md#1_staging)).
- `2_base`: preparation for **core**—entity resolution, shared identifiers, and first logical standardization across sources (unions/alignment where the same real-world entity appears in more than one staging place). Structural tests on grains and keys you define here—not the authoritative dimension/fact system of record (that is `3_core`).
- `3_core`: reusable business entities and clean relationship logic.
- `4_intermediate`: heavier transformations and feature engineering.
- `5_marts`: app/BI-ready outputs for consumption.

Further reading:

- Detailed layering rules: [dbt_project/docs/layering.md](dbt_project/docs/layering.md)
- Engineering standards: [dbt_project/docs/engineering_standards.md](dbt_project/docs/engineering_standards.md)
- API-Football data contract: [docs/data_contract.md](docs/data_contract.md)
- Development workflow: [docs/development_workflow.md](docs/development_workflow.md)

## Maintenance & operations

- **Runbook and troubleshooting** (environment variables, ingest lock, completeness checks, backfill vs daily update): [`docs/operations_guide.md`](docs/operations_guide.md).
- **Cursor / AI governance** (binding rules for tool use, edits, and permissions): [`.cursor/rules/ai-behavior-and-permissions.mdc`](.cursor/rules/ai-behavior-and-permissions.mdc).
