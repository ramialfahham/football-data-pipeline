# Data contract: API-Football → BigQuery (Bundesliga D1)

This page describes **what we store** in our first BigQuery layer and **how updates work**. It is written so both **non-technical readers** and **engineers** can rely on the same facts.

Official API references (for envelope shape, pagination, limits, and coverage flags):

- [API-Football v3 documentation](https://www.api-football.com/documentation-v3)
- [API-Football beginner’s guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide)

**League in scope:** **D1** — German Bundesliga (API-Football league id **78**).

---

## The landing zone (why we keep the full JSON)

Think of each API response as a **delivery of ingredients**: headers, parameters, errors, paging, and the main `response` body, all in one package.

Our **landing zone** is a set of BigQuery tables where we store those packages **as the API sent them** (inside a single JSON field called `payload`). We do **not** throw away fields we are not using yet in dashboards or models.

**In plain terms:** we keep the **original recipe card**, not only the few numbers we already put on a label. That way we never lose detail we might need later, and we can always re-parse the same snapshot if our staging models improve.

**Technical note:** each load stores one row per table with `payload` (JSON) and `ingested_datetime` (when that snapshot was written). Downstream **dbt** staging reads `payload` and treats `ingested_datetime` as `raw_ingested_datetime` where documented.

---

## How updates work (merge before each save)

Each run, our **Python ingestion** job:

1. **Reads** the latest stored `payload` from BigQuery for that table (when it exists).
2. **Combines** it with what the API returned **this** run—**keeping** data we already had and **adding or refreshing** pieces that belong to the same logical keys (for example the same match, club, or season block, depending on the table).
3. **Writes** the **combined** snapshot back as the new row for that table.

**In plain terms:** we look in the cupboard first, merge in what we just fetched, then put the **full merged box** back. We do **not** rely on “only this run’s slice” as the whole truth. That saves **repeat API calls** for data we already hold, and it lets a long backfill span **several days** under a daily request limit—the next run **continues** from what is already in BigQuery.

**Caveat in one sentence:** the API may still limit how much one **day** of calls can refresh; “complete” for heavy areas (like per-match detail) may take **multiple successful runs**, which is expected.

---

## Endpoints and raw tables (technical map)

Each row below is **one HTTP area** and the **BigQuery raw table** where its merged landing-zone payload lives (dataset id is usually `raw`; configurable with `API_FOOTBALL_BIGQUERY_DATASET`). Loads use **write truncate** on the **table**, but the **payload** inside is the **merged** cumulative snapshot described above.

| Area | Endpoint(s) | BigQuery raw table |
|------|----------------|-------------------|
| Fixtures | `/fixtures` | `RAW_D1_APIF_FIXTURES_NEXT` |
| League + coverage | `/leagues?id=` (all seasons in `seasons[]`) | `RAW_D1_APIF_LEAGUES` |
| Standings | `/standings` | `RAW_D1_APIF_STANDINGS` |
| Rounds | `/fixtures/rounds` | `RAW_D1_APIF_ROUNDS` |
| Teams | `/teams` | `RAW_D1_APIF_TEAMS` |
| Injuries | `/injuries` | `RAW_D1_APIF_INJURIES` |
| Top lists | `/players/topscorers`, `topassists`, `topyellowcards`, `topredcards` | `RAW_D1_APIF_TOPSCORERS`, `RAW_D1_APIF_TOPASSISTS`, `RAW_D1_APIF_TOPYELLOWCARDS`, `RAW_D1_APIF_TOPREDCARDS` |
| Transfers | `/transfers` (when league and season are accepted) | `RAW_D1_APIF_TRANSFERS` |
| Squad | `/players` per team, with `page=` merged where applicable | `RAW_D1_APIF_PLAYERS` |
| Per-fixture bundle | `/fixtures/lineups`, `/fixtures/events`, `/fixtures/statistics`, `/fixtures/players`, `/predictions` | `RAW_D1_APIF_LINEUPS`, `RAW_D1_APIF_FIXTURE_EVENTS`, `RAW_D1_APIF_FIXTURE_STATISTICS`, `RAW_D1_APIF_FIXTURE_PLAYERS`, `RAW_D1_APIF_PREDICTIONS` |

**`/fixtures` query style:** default is **`season`** (`league` + `season` only). Optional **`from_to`** or **`next`** modes exist for other use cases. Fixture **`page=`** is only used when **`API_FOOTBALL_FIXTURE_USE_PAGE=1`** (many plans do not support it).

**Pagination (`page=`):** merged for **`/players`**, top lists, and **`/transfers`** when the API paginates. **Not** sent by default for **`/fixtures`**, **`/teams`**, **`/injuries`**, **`/standings`** (friendlier on strict plans).

**Coverage:** where **`/leagues`** exposes coverage flags, ingestion can **skip** expensive calls (standings, injuries, per-fixture resources) when the API says they are not available for that season—see the beginner’s guide for envelope and flag behaviour.

---

## Plan vs product (what the subscription list maps to here)

| Your plan often includes | In this repo today |
|--------------------------|-------------------|
| Leagues, seasons (via league payload) | Yes — `GET /leagues`, seasons in `RAW_D1_APIF_LEAGUES` |
| Standings, teams, fixtures | Yes |
| Events | Yes — `GET /fixtures/events` (batched raw → staging) |
| Line-ups | Yes — `GET /fixtures/lineups` |
| Top scorers (+ assists / cards lists) | Yes — `GET /players/topscorers` and related top-list endpoints |
| Players & coaches | Partly — squad **`/players`** per club; coach may appear on lineup payloads where the API returns it; no separate “coaches only” ingest |
| Player transfers | Yes — `GET /transfers` by team |
| Injuries | Yes — `GET /injuries` |
| Pre-match / in-play odds | **Not in this repo** (no odds ingest) |
| Statistics | Yes — `GET /fixtures/statistics` and fixture player stats |
| Predictions | Yes — `GET /predictions` |
| Countries | Not ingested (would be `GET /countries` if added later) |
| Head to head | Not ingested (`GET /fixtures/headtohead` if added later) |
| Live score as a separate stream | Not a separate scheduled ingest; fixture refresh covers scheduled data |
| Trophies | Not ingested |
| Sidelined | Not ingested unless mapped explicitly later |

---

## Operational tables (not match data)

These tables support **safe scheduling**, not match statistics:

| Purpose | BigQuery table |
|---------|----------------|
| Single-flight ingest lock | `RAW_APIF_INGEST_LOCK` |
| Optional fanout cursor (rotating “where to continue”) | `RAW_D1_APIF_INGEST_CURSOR` |

---

## After landing zone

Cleaned, source-near columns for D1 live in **dbt** under `dbt_project/models/1_staging/api_football/`. For how layers are intended to stack, see `dbt_project/docs/layering.md` (outside this `docs/` folder).
