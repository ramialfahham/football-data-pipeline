# API-Football MVP Scope

This document defines the API-Football footprint for **Bundesliga (D1)** raw loads and staging.

Official references:

- [API-Football v3 documentation](https://www.api-football.com/documentation-v3)
- [How to get started with API-Football (complete beginner’s guide)](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) (envelope fields, pagination, rate limits, coverage flags, empty `response` on HTTP 200)

## Goal

Collect enough player context for fan-facing pre-match views without high API spend.

### Paid key: normal “warehouse” ingestion (best practice here)

The repo already loads **every raw table** in the table map below on each run, unless you explicitly turn pieces off (`SKIP_*` env vars).

1. Set **`API_FOOTBALL_API_KEY`**.
2. **Multi-season is the code default:** if **`API_FOOTBALL_INGEST_PROFILE` is unset**, ingestion behaves like **`full`** (all API-listed seasons for D1, paid-friendly caps via `setdefault`). Set **`API_FOOTBALL_INGEST_PROFILE=default`** (or **`economy`**) only for **free-tier** pacing and a **single** inferred season.
3. Set **`API_FOOTBALL_SEASON`** only when you intentionally want **one** season regardless of profile.

**What we cannot “magic away”:** the API may still cap **how many HTTP calls fit in one day**; per-fixture lineups/odds/etc. are budgeted from quota headers when present. If one run does not cover every fixture in every season, run again later or tune caps—same as any external API pipeline.

### API-Sports **Pro** plan (example: ~\$19/mo, **7 500 requests/day**)

Your subscription list maps to this repo **as follows** (D1-only MVP):

| Your plan includes | In this repo today |
|--------------------|--------------------|
| Leagues, Seasons (via league payload) | Yes — `GET /leagues`, seasons in `RAW_D1_APIF_LEAGUES` |
| Standings, Teams, Fixtures | Yes |
| Events | Yes — `GET /fixtures/events` (batched raw → staging) |
| LineUps | Yes — `GET /fixtures/lineups` |
| Top Scorers (+ assists / cards lists) | Yes — `GET /players/topscorers` (and related top lists) |
| Players & Coachs | Partly — squad **`/players`** per club (+ coach on lineup payload where API returns it); no separate “coaches only” table |
| Players Transfers | Yes — `GET /transfers` by team |
| Injuries | Yes — `GET /injuries` |
| Pre-match / in-play Odds | Pre-match per fixture — `GET /odds` (+ reference **`/odds/bookmakers`**, **`/odds/bets`**). In-play is the same odds surface from the API when offered for the fixture; we do not run a separate “live only” poller |
| Statistics | Yes — `GET /fixtures/statistics` (+ fixture player stats) |
| Predictions | Yes — `GET /predictions` |
| **Countries** | Not ingested (would be reference `GET /countries` — add if you need it) |
| **Head to head** | Not ingested (`GET /fixtures/headtohead` — add if you need it) |
| **Livescore** | Not a separate scheduled ingest (live scores are a different usage pattern; fixtures refresh covers scheduled data) |
| **Trophies** | Not ingested |
| **Sidelined** | Not ingested (separate from injuries unless you map it explicitly) |

**7 500 requests/day:** enough for steady production use, but **one** “full profile” run over **all seasons** plus **every** fixture’s lineups/events/odds/predictions can still exceed **7 500 HTTP calls** in a single day. Treat the daily cap like any warehouse limit: same job next day, split jobs (e.g. season slices), or lower fanout until coverage fits. Watch dashboard usage and 429s; set `API_FOOTBALL_REQUEST_PAUSE_MS` slightly above `0` only if you hit per-minute limits.

### How to scope work (so runs stay predictable)

Copy this block into a ticket or chat when you ask for changes:

- **Goal:** e.g. “Raw `football-data-pipeline-gcp.raw` populated enough to run `dbt` staging for D1.”
- **Non-goals:** e.g. “No multi-season archive yet”, “no in-play polling.”
- **Hard constraints:** e.g. “≤ 7 500 HTTP/day”, “single season `2025`”, “EU BigQuery only.”
- **Done when:** e.g. “`SELECT COUNT(*) FROM …raw…RAW_D1_APIF_FIXTURES_NEXT` > 0 and `dbt build --project-dir dbt_project --selector staging` succeeds.”

Ingestion prints **`[api-football] league=D1 phase=…`** between major steps (catalog, fixtures, standings, …) so a long run is not a silent hang.

### 7 500/day: default playbook to unblock dbt

**Idea:** one **bounded** day — **one season** of core tables + **capped** per-fixture work; widen caps or add days only after staging is green.

1. In repo-root **`.env`** (beside `API_FOOTBALL_API_KEY`), set at least:

   - `API_FOOTBALL_INGEST_PROFILE=default` — single inferred season, sane pacing (unset `API_FOOTBALL_REQUEST_PAUSE_MS` → ~6.6 s between calls unless you override).
   - `API_FOOTBALL_SEASON=2025` — **or** your real campaign start year (overrides inference).
   - **Do not** leave `API_FOOTBALL_INGEST_PROFILE` unset on a capped key (that selects **`full`** = all seasons + no pacing + fanout soft cap off).

2. **Cap expensive steps** until you know usage:

   - `API_FOOTBALL_LINEUPS_MAX_FIXTURES=200` — hard cap on how many fixtures get the lineups/events/stats/odds bundle (tune up/down).
   - `API_FOOTBALL_ODDS_MAX_PAGE=1` — fewer `/odds` pages per fixture.
   - Optional: `API_FOOTBALL_SKIP_ODDS_REFERENCE=1` if you do not need bookmaker/bet reference tables yet.

3. **Run** (from repo root): `PYTHONPATH=. python -m ingestion.api_football.main` — wait for **`Loaded N API-Football tables.`** (exit **0**) or read the printed **Notes** for API errors.

4. **Verify BigQuery** (Console or `bq`): table **`football-data-pipeline-gcp.raw.RAW_D1_APIF_FIXTURES_NEXT`** (and peers) exist; `payload` is not null.

5. **Staging:** `cd dbt_project` then `dbt build --selector staging` (profile must point at the same GCP project; `vars.raw_schema` = raw dataset id, default **`raw`**).

6. **Next days:** raise `LINEUPS_MAX_FIXTURES`, add `API_FOOTBALL_SEASONS=2023,2024,2025`, or switch to **`FANOUT_PRIORITY=cursor`** across scheduled runs (documented above) — still bounded, not one accidental “full” run.

## Endpoints and raw tables (D1)

League id **78**. Ingestion loads **all league-relevant endpoints** below; the [beginner’s guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) states the free plan includes **every endpoint** but only **~100 requests/day** — so per-fixture bundles are **capped** (see cost section).

**BigQuery raw contract:** each ingested table is **one row per truncate-load** with **`payload`** (JSON: full API envelope or batched wrapper) and **`ingested_datetime`** (UTC `TIMESTAMP` when the loader wrote that row). **Staging reads `payload` and exposes `ingested_datetime` as `raw_ingested_datetime`.** Calendar fields in staging use the **`_date`** / **`_datetime`** suffix convention (`DATE` vs `TIMESTAMP`). If a dataset still has older autodetect tables (top-level `response`, …), **re-run ingestion** (or drop and reload those tables) so the schema matches; dbt no longer supports a parallel “legacy raw” path.

**Diagnosis note:** if `RAW_D1_APIF_FIXTURES_NEXT` loads but **`json_value(payload, '$.response')`** is empty, the API returned no fixtures for that run (parameters, season window, errors, or quota)—staging cannot invent matches. Other endpoints can still populate normally.

| Area | Endpoint(s) | BigQuery raw table |
|------|-------------|-------------------|
| Fixtures | `/fixtures` | `RAW_D1_APIF_FIXTURES_NEXT` |
| League + coverage | `/leagues?id=` (all seasons returned in `seasons[]`) | `RAW_D1_APIF_LEAGUES` |
| Standings | `/standings` | `RAW_D1_APIF_STANDINGS` |
| Rounds | `/fixtures/rounds` | `RAW_D1_APIF_ROUNDS` |
| Teams | `/teams` | `RAW_D1_APIF_TEAMS` |
| Injuries | `/injuries` | `RAW_D1_APIF_INJURIES` |
| Top lists | `/players/topscorers`, `topassists`, `topyellowcards`, `topredcards` | `RAW_D1_APIF_TOPSCORERS`, … `_TOPASSISTS_`, `_TOPYELLOWCARDS_`, `_TOPREDCARDS_` |
| Transfers | `/transfers` (league+season when accepted) | `RAW_D1_APIF_TRANSFERS` |
| Odds reference | `/odds/bookmakers`, `/odds/bets` | `RAW_APIF_ODDS_BOOKMAKERS`, `RAW_APIF_ODDS_BETS` |
| Squad stats | `/players` per team, `page=` merged | `RAW_D1_APIF_PLAYERS` |
| Per-fixture bundle | `/fixtures/lineups`, `/fixtures/events`, `/fixtures/statistics`, `/fixtures/players`, `/predictions`, `/odds` | `RAW_D1_APIF_LINEUPS`, `RAW_D1_APIF_FIXTURE_EVENTS`, `RAW_D1_APIF_FIXTURE_STATISTICS`, `RAW_D1_APIF_FIXTURE_PLAYERS`, `RAW_D1_APIF_PREDICTIONS`, `RAW_D1_APIF_ODDS` |

**`/fixtures`:** default **`season`** (`league` + `season` only). Optional **`from_to`** or **`next`** (paid-friendly). Fixture **`page=`** only if **`API_FOOTBALL_FIXTURE_USE_PAGE=1`**.

**`page=`:** merged for **`/players`**, top lists, **`/transfers`** (when paginated), and **`/odds`** per fixture. **Not** sent for **`/fixtures`**, **`/teams`**, **`/injuries`**, **`/standings`** by default (free-friendly).

**Coverage:** responses from **`/leagues`** drive skips for standings, injuries, and per-fixture sub-resources when flags are false (see guide).

## League Scope

- **D1** — German Bundesliga only (API-Football league id `78`).

## Full-season archive **and** next-matchday freshness (economic)

On a **~100 requests/day** free key you cannot both (a) refresh **every** per-fixture endpoint for **every** season match **and** (b) pull full **/players** squads **every** run in one pass. The economical pattern is **split responsibilities across scheduled runs**, not one overloaded job.

1. **Keep `API_FOOTBALL_FIXTURES_MODE=season`** so each run still does **one** `/fixtures` call and refreshes **cheap league tables** (leagues, standings, rounds, teams, injuries, top lists, etc.). That preserves a **full-season fixture list** in BigQuery every day.

2. **Freshness (next matchdays):** leave **`API_FOOTBALL_FANOUT_PRIORITY=upcoming`** (default). The pipeline orders fixtures so those with kickoff in **`[today, today + API_FOOTBALL_FRESH_HORIZON_DAYS]`** are handled **first** before the per-fixture budget is spent. Tune **`API_FOOTBALL_FRESH_HORIZON_DAYS`** (default **14**) to your preview window.

3. **Archive (walk the rest of the season):** schedule a **second** daily (or weekly) run with **`API_FOOTBALL_FANOUT_PRIORITY=cursor`**. Ingestion reads **`RAW_D1_APIF_INGEST_CURSOR`**, walks the chronological fixture list in slices, and **writes the new offset** after each run so the next run continues where it stopped. Over many days you cover the full season for lineups / events / stats / predictions / odds **without** starving upcoming matches (when the “fresh” job runs with default priority).

4. **Save a large block of calls on archive runs:** set **`API_FOOTBALL_SKIP_PLAYERS=1`** on the **cursor** job only. Squad-level `/players` changes slowly; refresh it on the **upcoming** job (priority `upcoming`, skip unset). When players are skipped, the fanout budget **does not** reserve the usual per-club `/players` pages.

5. **When you outgrow free quota** while keeping the same code paths, move the same two schedules to a **paid** key (higher daily cap); the guide notes the same JSON shapes across plans.

## One-time “full archive” load (no scheduler yet)

Use this when you want a **single point-in-time snapshot** of as much D1 history as your key allows, then pause scheduling while you build **dbt** downstream. After you subscribe, revisit **scheduling** and (if needed) **append-only** tables for data that changes over time (odds, predictions).

**What “full archive” means here**

- With **enough daily quota in one run**, each raw table is still **truncate-reloaded**, but the payload can contain **the whole season** for that resource (e.g. every fixture in the fanout tables, full `/players` pages per club). That is a **complete static archive** for finished matches (stats, events, lineups after FT, etc.).
- You **do not** get multiple past versions of the same row in the same raw table unless you add a **history/append** layer later (optional follow-up).

**Paid key (recommended for one shot)** — minimal `.env`:

- `API_FOOTBALL_API_KEY` — paid dashboard key.
- `API_FOOTBALL_INGEST_PROFILE=full` — bundled paid defaults (all API-listed seasons, `REQUEST_PAUSE_MS=0`, higher page caps; see **Paid key** above).

Optional tweaks: `API_FOOTBALL_FANOUT_PRIORITY=season_chrono` for deterministic fixture order; set `API_FOOTBALL_SEASON=2024` if you only want one season; raise individual `*_MAX_PAGE` vars if the API still truncates and you need even more pages per resource.

Then run **`python -m ingestion.api_football.main`** once, then **`dbt build --project-dir .\dbt_project --selector staging`**.

**Free key (same “once”, but realistically multi-day)** — expect **many manual runs** or **`FANOUT_PRIORITY=cursor`** over days; raw per-fixture tables will only hold **the last run’s slice** until you upgrade or add append-only history.

## Cost Controls

- Default **`season`** fixtures = **one calendar’s worth of league fixtures** (not “next 20 only”), within whatever the API returns for `league` + `season`.
- **Free tier: one day vs “all data”.** Free keys are typically **~100 HTTP requests/day** and **10/min** ([guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide)). The **per-fixture bundle** is **capped** using `x-ratelimit-requests-remaining` (and **`API_FOOTBALL_FANOUT_PRIORITY`**: **upcoming** vs **cursor** — see previous section). **`/players`** is reserved unless **`API_FOOTBALL_SKIP_PLAYERS=1`**.
- Pacing defaults to stay under **10/min** (`API_FOOTBALL_REQUEST_PAUSE_MS` unset → ~6.6 s between successful calls).
- Batch schedule 2–4 times daily if you only need fresher snapshots (not required for “maximize one pull” experiments).

API responses always use the same envelope: check `errors`, then `paging`, then `response` (HTTP 200 can still mean empty results — wrong `season`, unsupported `next`, or no data yet). Ingestion aggregates body `errors` into the stored envelope (merges **`page=`** for **`/players`** and optionally for **`/fixtures`** when enabled), and appends human-readable notes to the function return message when the API reports issues.

## Environment Variables

- `API_FOOTBALL_INGEST_PROFILE` (optional): **`full`** (aliases **`paid`**, **`complete`**) applies standard **paid / warehouse** defaults via `setdefault`—all seasons the API lists, no pacing unless you set `REQUEST_PAUSE_MS`, higher pagination caps, fanout soft cap off. **`default`** / **`economy`** / **`free`** = conservative single-season ingestion with free-tier-friendly pacing. **If this variable is unset, ingestion defaults to `full`.** Legacy: **`API_FOOTBALL_PAID_FULL_LOAD=1`** is also treated like **`full`** when the profile name is unset.
- `API_FOOTBALL_API_KEY` (required): dashboard key from [API-Sports](https://dashboard.api-sports.io/) (header `x-apisports-key`), **or** RapidAPI key if you use that marketplace.
- `API_FOOTBALL_PROVIDER` (optional): `apisports` (default, direct `v3.football.api-sports.io`) or `rapidapi` (requires an active RapidAPI subscription to the API-Football product).
- `API_FOOTBALL_SEASON` (optional): competition season as **start year** (e.g. `2025` for 2025/26). When set, ingestion uses **exactly this year** for that league (no band filter).
- `API_FOOTBALL_SEASON_MIN` / `API_FOOTBALL_SEASON_MAX` (optional): bounds used when inferring or filtering seasons (defaults **`1990`** .. **current calendar year**). Narrow them if your key only allows a historical band (e.g. free-tier messages such as *“try from 2022 to 2024”* → set both min and max accordingly).
- `API_FOOTBALL_ALL_SEASONS` (optional): **`1`** / **`true`** / **`yes`** / **`on`** — same multi-season discovery as **`INGEST_PROFILE=full`**: every season year from `GET /leagues?id=…` (plus `GET /leagues/seasons?league=` if the catalog lists fewer than two years), intersected with `SEASON_MIN`/`SEASON_MAX`. **High quota cost.** With **`INGEST_PROFILE` unset**, you already get this behavior (full is the code default); use **`INGEST_PROFILE=default`** for a single inferred season without setting this flag.
- `API_FOOTBALL_SEASONS` (optional): comma-separated start years (e.g. `2022,2023,2024,2025`) when you want an explicit subset; filtered by `SEASON_MIN`/`MAX` unless **`API_FOOTBALL_SEASON`** is set (which wins earlier in precedence).
- **Single inferred season:** set **`API_FOOTBALL_INGEST_PROFILE=default`** (or **`economy`**) and leave `SEASON` / `SEASONS` / `ALL_SEASONS` unset (or do not force full profile). Ingestion then uses the **current** campaign from UTC with a **1 July** boundary, clamped to `SEASON_MIN`..`SEASON_MAX`.
- `API_FOOTBALL_FIXTURES_MODE` (optional): **`season`** (default — `league` + `season` only), **`from_to`** (rolling or explicit `from`/`to`), or **`next`** (`next=20`; typically **paid** only — free plans often return *“do not have access to the Next parameter”*).
- `API_FOOTBALL_FIXTURE_USE_PAGE` (optional): set to `1` / `true` / `yes` to send **`page=`** on **`/fixtures`** when mode is **`season`** (many **free** plans **reject** fixture `page` — leave unset unless you confirmed paging works on your key).
- `API_FOOTBALL_FIXTURES_MAX_PAGE` (optional, default **`50`**): safety cap when **`API_FOOTBALL_FIXTURE_USE_PAGE`** is enabled.
- `API_FOOTBALL_FIXTURE_FROM` / `API_FOOTBALL_FIXTURE_TO` (optional, with `from_to`): inclusive `yyyy-MM-dd` bounds. If omitted, ingestion uses the last **`API_FOOTBALL_FIXTURE_RANGE_DAYS`** days inside the API **`season`**, capped by **UTC today**, **June 30 `season+1`**, and **May 31 `season+1`** (so the default window does not sit in the summer break when many leagues return **no** league fixtures).
- `API_FOOTBALL_FIXTURE_RANGE_DAYS` (optional, default **`42`**): length of that rolling window (calendar days, inclusive span). Used only when **`API_FOOTBALL_FIXTURES_MODE=from_to`**. Increase (e.g. `90`) for more fixtures per run; use explicit **`FIXTURE_FROM` / `TO`** for a slice.
- `API_FOOTBALL_LINEUPS_MAX_FIXTURES` (optional): hard cap on how many fixtures enter the **per-fixture bundle** (same cap for lineups, events, statistics, etc., in one run).
- `API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER` (optional, default **`6`**): when **`x-ratelimit-requests-remaining`** is missing, max fixtures in the bundle (set **`-1`** to disable).
- `API_FOOTBALL_ODDS_MAX_PAGE` (optional, default **`3`**): max **`page=`** calls per fixture for **`/odds`** (guide: 10 odds rows per page).
- `API_FOOTBALL_TOP_LISTS_MAX_PAGE` (optional): **ignored** in ingestion — top-list endpoints (`/players/topscorers`, etc.) are called **without** `page=` because many keys (including free tier) return *“The Page field do not exist”*.
- `API_FOOTBALL_FETCH_TRANSFERS` (optional): default **`1`**; set to **`0`** / **`false`** / **`no`** to skip **`/transfers`** (saves quota if the call fails or is unused).
- `API_FOOTBALL_TRANSFERS_MAX_PAGE` (optional, default **`3`**): page cap for **`/transfers`** when paginated.
- `API_FOOTBALL_SKIP_ODDS_REFERENCE` (optional): **`1`** / **`true`** / **`yes`** to skip **`/odds/bookmakers`** and **`/odds/bets`**.
- `API_FOOTBALL_QUOTA_BUFFER` (optional, default **`5`**): extra requests reserved when computing the fixture bundle size before **`/players`**.
- `API_FOOTBALL_BIGQUERY_DATASET` (optional): BigQuery **dataset id** for 1:1 ingestion tables (default **`raw`**). Must match dbt **`raw_schema`** (see `vars` in [`dbt_project/dbt_project.yml`](../dbt_project/dbt_project.yml) and `schema` in [`dbt_project/models/1_staging/api_football/sources.yml`](../dbt_project/models/1_staging/api_football/sources.yml)). Legacy deployments used **`API_FOOTBALL`** — set this env to that name if you keep the old dataset.
- `API_FOOTBALL_DATASET_LOCATION` (optional): BigQuery **region** for the raw dataset when it is first created (default **`EU`**, same as `location` in [`dbt_project/profiles.example.yml`](dbt_project/profiles.example.yml)). If the dataset already exists elsewhere, delete it once or align dbt’s `location` with that region.
- `API_FOOTBALL_MAX_PAGES` (optional, default **`250`**): safety cap when merging `page=` results for **`/players`**.
- `API_FOOTBALL_REQUEST_PAUSE_MS` (optional): milliseconds to sleep **after each successful** HTTP response. **If unset**, defaults to **6600** (~9 calls/min) so free-tier **10 req/min** limits are less likely to trip. Set to **`0`** for no pause (typical on **paid** plans or CI).
- `API_FOOTBALL_PLAYERS_MAX_PAGE` (optional, default **3**): last `page` number to request per team for `/players` (free tier often allows pages **1–3** only).
- `API_FOOTBALL_LOG_QUOTA` (optional): set to `1` / `true` / `yes` to print `x-ratelimit-requests-remaining` and per-minute remaining headers after each call (stdout).
- `API_FOOTBALL_FANOUT_PRIORITY` (optional): **`upcoming`** (default — next **`API_FOOTBALL_FRESH_HORIZON_DAYS`** window first), **`season_chrono`** / **`chrono`** (earliest kickoff first for the whole list), or **`cursor`** (rotate from offset stored in **`RAW_D1_APIF_INGEST_CURSOR`** for systematic archive passes).
- `API_FOOTBALL_FRESH_HORIZON_DAYS` (optional, default **`14`**): calendar days ahead of UTC **today** treated as “fresh” when **`FANOUT_PRIORITY=upcoming`**.
- `API_FOOTBALL_SKIP_PLAYERS` (optional): **`1`** / **`true`** / **`yes`** to skip **`/players`** pulls (saves **`teams × pages`** calls; use on low-quota **cursor** runs).

## Local ingestion (no Cloud Run)

From repo root, with [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) for the project.

**API key once (no paste every run):** copy [`.env.example`](../.env.example) to **`.env`** in the repo root, set `API_FOOTBALL_API_KEY=...`, and `pip install -r requirements.txt` (includes `python-dotenv`). Ingestion loads `.env` automatically. **Never commit `.env`** (it is gitignored).

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = "."
python -m ingestion.api_football.main
```

Or set `API_FOOTBALL_API_KEY` in the shell / OS user environment if you prefer not to use a file.

Creates the **raw** dataset (default id **`raw`**; override with `API_FOOTBALL_BIGQUERY_DATASET`) in **EU** by default, then loads **all** `RAW_D1_APIF_*` league tables listed above (plus global **`RAW_APIF_ODDS_*`** reference tables). See [`dbt_project/docs/layering.md`](../dbt_project/docs/layering.md) for how this maps to **staging → base → core → intermediate → marts** datasets.

On a **free** key, the first full run can take **several minutes** (default pacing ~10 HTTP calls/min and up to three `/players` pages per club). Then run **`dbt build --project-dir .\dbt_project --selector staging`** so BigQuery `staging` views match the new raw rows.

## Data Flow

1. Ingestion writes raw payload snapshots to the **`raw`** BigQuery dataset (D1 tables only; configurable via `API_FOOTBALL_BIGQUERY_DATASET`).
2. `1_staging/api_football` models expose cleaned, source-near columns for D1.
3. Downstream layers (`2_base`–`5_marts`) are intentionally empty in the MVP repo; add models when you define analytics and marts.

## Optional BigQuery cleanup (multi-league raw tables)

If you still have **E0 / I1 / SP1 / F1** raw tables from older runs, drop them with the checked-in script (edit project id if needed): [`scripts/bigquery_drop_non_d1_raw_tables.sql`](../scripts/bigquery_drop_non_d1_raw_tables.sql). Run it in the BigQuery console (multi-statement) or via `bq query --use_legacy_sql=false < scripts/bigquery_drop_non_d1_raw_tables.sql`.
