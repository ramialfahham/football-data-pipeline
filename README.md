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

**Competition scope:** ingestion and dbt models target **German Bundesliga (D1)** only (API-Football league id **78**). Adding a second competition means adding raw tables with a new league prefix and a parallel set of staging models; the `3_core` layer is already `league_code`-aware so dims and facts can union future leagues without schema changes.

**Layer population (current state):**

| Layer | Status | What is there |
|-------|--------|---------------|
| `1_staging` | populated | 17 `stg_apif__d1_*` models, one per `RAW_D1_APIF_*` source. |
| `2_base` | empty placeholder | Deferred until a second landing source exists. |
| `3_core` | populated | 5 dims (`dim_date`, `dim_league`, `dim_season`, `dim_team`, `dim_player`), 6 facts (`fct_fixture`, `fct_standings`, `fct_fixture_team_stats`, `fct_fixture_player_stats`, `fct_fixture_event`, `fct_transfer`), 1 snapshot (`snap_apif_d1_standings`). |
| `4_intermediate` | 1 model | `int_apif__raw_ingestion_spread` (ingestion-spread audit). |
| `5_marts` | empty placeholder | Built on demand once a consumer is defined. |

Until `2_base` and `5_marts` contain models, `dbt parse` / `dbt build` may warn that their folder configs apply to no resources; that is expected.

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

# Snapshot history tables first (standings), then all downstream (core + intermediate)
dbt snapshot --project-dir .\dbt_project
dbt build   --project-dir .\dbt_project --selector downstream

# Full suite (staging + downstream + tests)
dbt build --project-dir .\dbt_project

# Selector "base" and "marts" are defined but currently match no models.
# dbt build --project-dir .\dbt_project --selector base
# dbt build --project-dir .\dbt_project --selector marts

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
- **Cursor / AI governance:** three focused rule files in [`.cursor/rules/`](.cursor/rules/) — [`agent-behavior.mdc`](.cursor/rules/agent-behavior.mdc) and [`project-context.mdc`](.cursor/rules/project-context.mdc) always apply; [`dbt.mdc`](.cursor/rules/dbt.mdc) and [`ingestion.mdc`](.cursor/rules/ingestion.mdc) load only when the agent is editing files in the matching directory. Rules encode evergreen intent and point at the authoritative docs rather than duplicating them.
