# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ELT pipeline ingesting German Bundesliga (D1, league id 78) data from the API-Football service into Google BigQuery, then transforming it with dbt. Scope is intentionally narrow — Bundesliga only, API-Football only. Do not expand competition scope or add new data sources without explicit user confirmation.

## Development Commands

### Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
dbt deps --project-dir .\dbt_project
```

### Running Ingestion
```powershell
$env:PYTHONPATH = "."
python -m ingestion.api_football.main
```
Exit codes: `0` success, `1` pipeline error, `2` lock held (409), `3` incomplete (503).

### dbt Builds
```powershell
dbt build --project-dir .\dbt_project --selector staging        # staging layer only
dbt build --project-dir .\dbt_project --selector downstream     # base through marts
dbt build --project-dir .\dbt_project --selector dq             # all models + all tests
dbt build --project-dir .\dbt_project                           # full build
dbt snapshot --project-dir .\dbt_project                        # standings SCD2 snapshot
```

### Validation (run before pushing)
```powershell
# Syntax check — no BigQuery calls
dbt parse --project-dir .\dbt_project

# SQL lint — must run from dbt_project/ so dbt templater resolves Jinja
cd dbt_project && sqlfluff lint models

# Layer contract (exactly 13 staging models, no JSON extraction in core)
python scripts/check_layer_contract.py

# Ingestion wiring smoke test
python -m unittest tests.test_ingestion_loads_smoke
```

### Single dbt Model / Test
```powershell
dbt build --project-dir .\dbt_project --select stg_apif__d1_fixtures_next
dbt test  --project-dir .\dbt_project --select stg_apif__d1_fixtures_next
```

### Troubleshooting
```powershell
# Clear stale lock only when no job is running
python scripts/clear_apif_ingest_lock.py

# Manual completeness check
python scripts/data_trust_fixture_stats.py
```

## Architecture

### Data Flow
```
API-Football HTTP API
        ↓
Python Ingestion  (ingestion/api_football/)
        ↓ merge-on-write, WRITE_TRUNCATE
BigQuery raw dataset  (13 RAW_D1_APIF_* tables)
        ↓
dbt 1_staging  → views, JSON extraction, light cleanup  (13 models, 1:1 with raw tables)
dbt 3_core     → canonical dims + facts, no JSON ops    (11 models: 5 dims, 6 facts)
dbt 4_intermediate → complex joins, audits              (1 model)
```
`2_base` and `5_marts` layers exist as empty placeholders.

### Python Ingestion (`ingestion/api_football/`)

**Key concept — merge-on-write**: Each raw table holds a single row with a JSON `payload` column. The loader reads the prior payload from BigQuery (using the Storage Read API for large rows), merges the new API response into it in Python, then writes back with `WRITE_TRUNCATE`. This makes every run idempotent and supports partial multi-day runs under API rate limits.

**Entrypoint**: `main.py` → `league_pipeline.py` orchestrates per-league runs in this order:
1. `fixtures_load.py` — `/fixtures` (full season envelope)
2. `standings_load.py`, `rounds_load.py`, `teams_load.py`, `injuries_load.py`, `transfers_load.py`
3. `fixture_fanout_load.py` — per-fixture endpoints (lineups, events, statistics, players, predictions); skips already-covered fixtures
4. `squad_players_load.py` — batch `/players` per team

**Important classes**:
- `PipelineContext` — carries BigQuery client, API auth headers, error list, and loaded-table count
- `config.py` — env var loading, ingest profiles (`full` / `economy`), season window (10-year lookback)
- `http_client.py` — GET with retry, pagination merge, quota header tracking
- `payload_merge.py` — merge helpers named `merge_<entity>_<shape>` (e.g., `merge_fixtures_envelope`)
- `completeness.py` — post-run check that per-match tables cover all finished fixtures
- `ingestion_lock.py` — single-flight lock via `RAW_APIF_INGEST_LOCK` BigQuery table

### dbt Transform (`dbt_project/`)

**Layer contract (enforced in CI)**:
- `1_staging`: Exactly 13 models — one per raw source, no helpers, no unions. All JSON extraction happens here.
- `3_core`: No `json_value`, `json_query`, or `unnest` — JSON must be fully resolved before this layer.

**Schema mapping**: `macros/generate_schema_name.sql` maps layer folder names directly to BigQuery dataset ids. The `raw_schema` dbt variable (default `raw`) tells staging models where to find the raw tables.

**Snapshots**: `snap_apif_d1_standings` provides Type-2 SCD history for league standings.

**Testing policy**: staging models have `not_null` + `unique` on grain keys; core models add `relationships` and business-rule tests. See `dbt_project/docs/engineering_standards.md`.

## Key Configuration

| File | Purpose |
|------|---------|
| `.env` | `API_FOOTBALL_API_KEY`, `API_FOOTBALL_INGEST_PROFILE`, `API_FOOTBALL_BIGQUERY_DATASET` |
| `dbt_project/dbt_project.yml` | Materialization per layer, `raw_schema` var |
| `dbt_project/profiles.example.yml` | BigQuery auth template (copy to `~/.dbt/profiles.yml`) |
| `dbt_project/selectors.yml` | `staging`, `base`, `downstream`, `dq` selectors |
| `.sqlfluff` | BigQuery dialect, dbt templater, 120-char line limit |
| `ingestion/api_football/config.py` | League ids, season window, ingest profiles |

**Ingest profiles** (set via `API_FOOTBALL_INGEST_PROFILE`):
- `full` — multi-season, high fixture cap; for production runs
- `economy` / `default` — single season, fixture cap 6; for free-tier API keys and local dev

## CI/CD

GitHub Actions workflows:
- **`dbt-ci.yml`** — on PR/push: validates staging + select core, layer contract, SQL lint, fixture stats diagnostics
- **`dbt-scheduled.yml`** — nightly (4am + 4pm UTC): full `dq` build with all tests
- **`pages-match-preview.yml`** — deploys static match preview HTML to GitHub Pages
- **`security-secrets.yml`** — gitleaks secret scan

GCP authentication in Actions uses Workload Identity Federation (no long-lived service account keys).

## Authoritative Documentation

For deeper context before making significant changes:
- `docs/data_contract.md` — merge-on-write design, fanout selection, completeness definition
- `docs/operations_guide.md` — full env var reference, exit codes, lock management
- `docs/development_workflow.md` — local validation steps, pre-commit setup
- `dbt_project/docs/layering.md` — layer responsibilities, grain, BigQuery layout
- `dbt_project/docs/engineering_standards.md` — naming conventions, SQL structure, testing policy per layer
