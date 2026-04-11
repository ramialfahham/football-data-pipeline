# API-Football MVP Scope

This document defines the minimum API-Football footprint for player-focused pre-match insights.

## Goal

Collect enough player context for fan-facing pre-match views without high API spend.

## Endpoints in Scope

- `/fixtures` with `next=20` per league (or `from_to` when configured)
  - raw table: `RAW_APIF_FIXTURES_NEXT_D1`
- `/players` per team for teams in upcoming fixtures
  - raw table: `RAW_APIF_PLAYERS_D1`
- `/fixtures/lineups` per upcoming fixture
  - raw table: `RAW_APIF_LINEUPS_D1`
- `/injuries` per league/season
  - raw table: `RAW_APIF_INJURIES_D1`

## League Scope

- **D1** — German Bundesliga only (API-Football league id `78`).

## Cost Controls

- Only upcoming fixtures (no full-season exhaustive pulls).
- Only player pulls for teams appearing in those fixtures.
- Batch schedule 2-4 times daily (not live minute-by-minute).

## Environment Variables

- `API_FOOTBALL_API_KEY` (required): dashboard key from [API-Sports](https://dashboard.api-sports.io/) (header `x-apisports-key`), **or** RapidAPI key if you use that marketplace.
- `API_FOOTBALL_PROVIDER` (optional): `apisports` (default, direct `v3.football.api-sports.io`) or `rapidapi` (requires an active RapidAPI subscription to the API-Football product).
- `API_FOOTBALL_SEASON` (optional): competition season as **start year** (e.g. `2024` for 2024/25). Defaults to **previous calendar year** (`utcnow().year - 1`). Free plans may only allow a limited year range; set this explicitly if responses return empty `response` with an `errors` object.
- `API_FOOTBALL_FIXTURES_MODE` (optional): `next` (default, `next=20` — often **not** available on free tier) or `from_to` (uses `from` / `to` dates).
- `API_FOOTBALL_FIXTURE_FROM` / `API_FOOTBALL_FIXTURE_TO` (optional, with `from_to`): inclusive `yyyy-MM-dd` bounds. If omitted, defaults to **last N calendar days ending today**, with `API_FOOTBALL_FIXTURE_RANGE_DAYS` (default `14`). For free tiers you may need a **historical** window that matches an allowed `API_FOOTBALL_SEASON` (e.g. season `2024` with dates in 2024/25).
- `API_FOOTBALL_DATASET_LOCATION` (optional): BigQuery **region** for the `API_FOOTBALL` dataset when it is first created (default **`EU`**, same as `location` in [`dbt_project/profiles.example.yml`](dbt_project/profiles.example.yml)). If the dataset already exists elsewhere, delete it once or align dbt’s `location` with that region.

## Local ingestion (no Cloud Run)

From repo root, with [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) for the project and `API_FOOTBALL_API_KEY` set:

```powershell
$env:PYTHONPATH = "."
$env:API_FOOTBALL_API_KEY = "<your-key>"
python -m ingestion.api_football.main
```

Creates `API_FOOTBALL` in **EU** by default (override with `API_FOOTBALL_DATASET_LOCATION` if your dbt profile uses another region), then loads the four `RAW_APIF_*_D1` tables.

## Data Flow

1. Ingestion writes raw payload snapshots to the `API_FOOTBALL` dataset (D1 tables only).
2. `1_staging/api_football` models expose cleaned, source-near columns for D1.
3. Downstream layers (`2_base`–`5_marts`) are intentionally empty in the MVP repo; add models when you define analytics and marts.

## Optional BigQuery cleanup (multi-league raw tables)

If you still have **E0 / I1 / SP1 / F1** raw tables from older runs, drop them with the checked-in script (edit project id if needed): [`scripts/bigquery_drop_non_d1_raw_tables.sql`](../scripts/bigquery_drop_non_d1_raw_tables.sql). Run it in the BigQuery console (multi-statement) or via `bq query --use_legacy_sql=false < scripts/bigquery_drop_non_d1_raw_tables.sql`.
