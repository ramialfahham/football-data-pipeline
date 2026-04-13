# API-Football MVP Scope

This document defines the minimum API-Football footprint for player-focused pre-match insights.

Implementation follows the official walkthrough: [How to get started with API-Football (complete beginner’s guide)](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) (envelope fields, pagination, rate limits, empty `response` on HTTP 200).

## Goal

Collect enough player context for fan-facing pre-match views without high API spend.

## Endpoints in Scope

- `/fixtures`: default **`from_to`** (last N days ending today, or explicit `from`/`to`) — free plans usually reject **`next`**. One API request per run (**no `page`**; many plans error on `page` for this endpoint).
  - raw table: `RAW_APIF_FIXTURES_NEXT_D1` (name kept for history). Set `API_FOOTBALL_FIXTURES_MODE=next` on paid plans if you rely on `next=20`.
- `/teams` with `league` + `season` **only when** the fixtures response yields no team IDs (e.g. empty window, off-season). **One request, no `page`** (same free-tier `page` limitation as injuries).
- `/players` per team (`team` + `season`), **`page=` merged** up to **`API_FOOTBALL_PLAYERS_MAX_PAGE`** (default **3** — free plans often cap `page` at 3). Raise on paid plans if squads need more pages.
  - raw table: `RAW_APIF_PLAYERS_D1`
- `/fixtures/lineups` per upcoming fixture
  - raw table: `RAW_APIF_LINEUPS_D1`
- `/injuries` per league/season — **one request** (**no `page`**; free tier often returns *“The Page field do not exist”* if `page` is sent).
  - raw table: `RAW_APIF_INJURIES_D1`

## League Scope

- **D1** — German Bundesliga only (API-Football league id `78`).

## Cost Controls

- Only upcoming fixtures (no full-season exhaustive pulls).
- Player pulls target teams from **upcoming fixtures first**; if that set is empty, one `/teams` batch per league plus `/players` per club (still bounded by league size, not a global crawl).
- Batch schedule 2-4 times daily (not live minute-by-minute).

API responses always use the same envelope: check `errors`, then `paging`, then `response` (HTTP 200 can still mean empty results — wrong `season`, unsupported `next`, or no data yet). Ingestion aggregates body `errors` into the stored envelope (and merges **`page=`** only for **`/players`**), and appends human-readable notes to the function return message when the API reports issues.

## Environment Variables

- `API_FOOTBALL_API_KEY` (required): dashboard key from [API-Sports](https://dashboard.api-sports.io/) (header `x-apisports-key`), **or** RapidAPI key if you use that marketplace.
- `API_FOOTBALL_PROVIDER` (optional): `apisports` (default, direct `v3.football.api-sports.io`) or `rapidapi` (requires an active RapidAPI subscription to the API-Football product).
- `API_FOOTBALL_SEASON` (optional): competition season as **start year** (e.g. `2025` for 2025/26). **Set this when you move to a paid plan** so ingestion tracks the real current season. If omitted, ingestion uses `utcnow().year - 1` and **clamps** it to the free-tier window below so local runs keep working on a free key without per-year edits.
- `API_FOOTBALL_SEASON_MIN` / `API_FOOTBALL_SEASON_MAX` (optional): bounds used **only when `API_FOOTBALL_SEASON` is unset** (defaults **`2022`** and **`2024`** to match common API-Sports free-plan messages such as *“try from 2022 to 2024”*). On a paid plan, either set **`API_FOOTBALL_SEASON`** explicitly each season, or set a wide max (e.g. `API_FOOTBALL_SEASON_MAX=2099`) if you want auto `year-1` without clamping.
- `API_FOOTBALL_FIXTURES_MODE` (optional): **`from_to`** (default) or **`next`** (`next=20`; typically **paid** only — free plans often return *“do not have access to the Next parameter”*).
- `API_FOOTBALL_FIXTURE_FROM` / `API_FOOTBALL_FIXTURE_TO` (optional, with `from_to`): inclusive `yyyy-MM-dd` bounds. If omitted, ingestion uses the last **`API_FOOTBALL_FIXTURE_RANGE_DAYS`** days inside the API **`season`**, capped by **UTC today**, **June 30 `season+1`**, and **May 31 `season+1`** (so the default window does not sit in the summer break when many leagues return **no** league fixtures).
- `API_FOOTBALL_DATASET_LOCATION` (optional): BigQuery **region** for the `API_FOOTBALL` dataset when it is first created (default **`EU`**, same as `location` in [`dbt_project/profiles.example.yml`](dbt_project/profiles.example.yml)). If the dataset already exists elsewhere, delete it once or align dbt’s `location` with that region.
- `API_FOOTBALL_MAX_PAGES` (optional, default `250`): safety cap when merging `page=` results for **`/players`** only (other listed endpoints use a single request without `page` on free-friendly defaults).
- `API_FOOTBALL_REQUEST_PAUSE_MS` (optional): milliseconds to sleep **after each successful** HTTP response. **If unset**, defaults to **6600** (~9 calls/min) so free-tier **10 req/min** limits are less likely to trip. Set to **`0`** for no pause (typical on **paid** plans or CI).
- `API_FOOTBALL_PLAYERS_MAX_PAGE` (optional, default **3**): last `page` number to request per team for `/players` (free tier often allows pages **1–3** only).
- `API_FOOTBALL_LOG_QUOTA` (optional): set to `1` / `true` / `yes` to print `x-ratelimit-requests-remaining` and per-minute remaining headers after each call (stdout).

## Local ingestion (no Cloud Run)

From repo root, with [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) for the project.

**API key once (no paste every run):** copy [`.env.example`](../.env.example) to **`.env`** in the repo root, set `API_FOOTBALL_API_KEY=...`, and `pip install -r requirements.txt` (includes `python-dotenv`). Ingestion loads `.env` automatically. **Never commit `.env`** (it is gitignored).

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = "."
python -m ingestion.api_football.main
```

Or set `API_FOOTBALL_API_KEY` in the shell / OS user environment if you prefer not to use a file.

Creates `API_FOOTBALL` in **EU** by default (override with `API_FOOTBALL_DATASET_LOCATION` if your dbt profile uses another region), then loads the four `RAW_APIF_*_D1` tables.

On a **free** key, the first full run can take **several minutes** (default pacing ~10 HTTP calls/min and up to three `/players` pages per club). Then run **`dbt build --project-dir .\dbt_project --selector staging`** so BigQuery `staging` views match the new raw rows.

## Data Flow

1. Ingestion writes raw payload snapshots to the `API_FOOTBALL` dataset (D1 tables only).
2. `1_staging/api_football` models expose cleaned, source-near columns for D1.
3. Downstream layers (`2_base`–`5_marts`) are intentionally empty in the MVP repo; add models when you define analytics and marts.

## Optional BigQuery cleanup (multi-league raw tables)

If you still have **E0 / I1 / SP1 / F1** raw tables from older runs, drop them with the checked-in script (edit project id if needed): [`scripts/bigquery_drop_non_d1_raw_tables.sql`](../scripts/bigquery_drop_non_d1_raw_tables.sql). Run it in the BigQuery console (multi-statement) or via `bq query --use_legacy_sql=false < scripts/bigquery_drop_non_d1_raw_tables.sql`.
