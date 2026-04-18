# Data contract: API-Football → BigQuery (Bundesliga D1)

League in scope: **D1**, German Bundesliga, API-Football league id `78`.

API references:

- [API-Football v3 documentation](https://www.api-football.com/documentation-v3)
- [API-Football beginner's guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide)

---

## Landing zone

Each API-Football endpoint returns a JSON envelope: `get`, `parameters`, `errors`, `results`, `paging`, and a `response` array. The landing zone stores that envelope unchanged. Every raw table holds a single JSON column `payload` and a UTC `ingested_at` timestamp. Nothing is discarded at ingest, so new fields become available to modelling without refetching.

dbt staging reads `payload` and exposes `ingested_at` as `raw_ingested_at`.

---

## Merge-on-write

On every run, each raw table is written in three steps:

1. Read the latest `payload` from BigQuery.
2. Merge that prior `payload` in memory with the envelope the API returned this run, keyed by the table's logical identity (fixture id, team-season block, and so on).
3. Write the combined envelope back with `WRITE_TRUNCATE`.

Row count per table stays at one by design. Growth happens inside `payload.response` as more keys accumulate across runs. This keeps merge logic in Python, staging SQL simple, and re-ingests idempotent. Under a daily request limit the next run continues from what is already in BigQuery instead of starting over.

---

## Fanout selection (completeness-driven)

The five per-match raw tables (`RAW_D1_APIF_LINEUPS`, `RAW_D1_APIF_FIXTURE_EVENTS`, `RAW_D1_APIF_FIXTURE_STATISTICS`, `RAW_D1_APIF_FIXTURE_PLAYERS`, `RAW_D1_APIF_PREDICTIONS`) dominate the daily request budget. Before the per-fixture pass, the loader reads the current merged payloads for those five tables and extracts the set of fixture ids already covered, per endpoint. Only fixtures where at least one endpoint is still missing enter the ordering and budget math. Inside the loop, each individual endpoint call is skipped when that fixture id is already covered for that endpoint.

A start-of-phase log line reports what the run will attempt:

```
[api-football] fanout_selection league=D1 target=3074 already_complete=1501 missing_any_endpoint=1573
```

Coverage advances monotonically across runs under any ordering (`upcoming`, `cursor`, `chrono`). Once every in-scope fixture is covered across all five endpoints, the fanout pass is a no-op.

---

## Data completeness

Data is complete when four conditions hold:

1. **Coverage** — every in-scope raw table for D1 has been refreshed, and staging has been rebuilt on top of that refresh.
2. **History** — raw tables carry the multi-season window configured in `ingestion/api_football/config.py` (currently the last ten Bundesliga start years through the current campaign; see `V1_SEASON_WINDOW_YEARS`).
3. **Freshness** — when new source data appears (matchdays, injuries, transfers), the next run merges it into the corresponding raw tables.
4. **Query truth** — queries against raw or staging reflect the latest successful run, not a partial update in flight.

Heavy per-match coverage typically takes several runs under daily API limits; that is expected behaviour, not an outage. Each check below answers one of the four conditions:

| Question | Mechanism |
|----------|-----------|
| Did each raw table load recently? | dbt source freshness on `ingested_at` in `dbt_project/models/1_staging/api_football/sources.yml`. |
| Are raw tables' latest loads aligned with each other? | dbt model `int_apif__raw_ingestion_spread` (max `ingested_at` per table, `spread_minutes`). |
| Does staging reflect the latest raw? | Run `dbt build` for staging after a successful ingest. |
| Do per-match tables cover all fixtures in the merged list? | Post-ingest check in `ingestion/api_football/completeness.py`, logged as `ingest_completeness_json`. The field `match_level_tables_cover_all_fixtures` (legacy `all_fanout_complete`) is the boolean result. |

Operational detail (locks, exit codes, env vars) lives in [`operations_guide.md`](operations_guide.md).

---

## Endpoints and raw tables

Each row is one HTTP area and the BigQuery raw table where its merged payload lives. Dataset id defaults to `raw`, configurable via `API_FOOTBALL_BIGQUERY_DATASET`. Writes use `WRITE_TRUNCATE` on the table; the `payload` inside is the merged cumulative snapshot described above.

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

### /fixtures query style

Default is `season` (`league` + `season` only). Alternative modes `from_to` and `next` exist for other use cases; `next` typically requires a paid plan. Fixture paging (`page=`) is only sent when `API_FOOTBALL_FIXTURE_USE_PAGE=1`, because many plans reject it.

### Pagination

`page=` is merged for `/players` and the top-list endpoints when the API paginates. It is not sent by default on `/fixtures`, `/teams`, `/injuries`, `/standings`, or `/transfers`, because many plans reject paging on those endpoints with `"The Page field do not exist."`. Opt in per endpoint with `API_FOOTBALL_FIXTURE_USE_PAGE=1` or `API_FOOTBALL_TRANSFERS_USE_PAGE=1` only when the key is known to support it.

### Coverage flags

`/leagues` exposes `coverage` flags per season. When a flag says the API does not provide a resource for that season (standings, injuries, per-fixture events, etc.), ingestion skips the corresponding calls instead of spending quota on guaranteed-empty responses. See the beginner's guide for envelope and flag behaviour.

---

## Plan vs product

Mapping from a typical API-Football subscription list to what this repository ingests today.

| Your plan often includes | In this repo today |
|--------------------------|-------------------|
| Leagues, seasons (via league payload) | Yes — `GET /leagues`, seasons in `RAW_D1_APIF_LEAGUES` |
| Standings, teams, fixtures | Yes |
| Events | Yes — `GET /fixtures/events` (batched raw → staging) |
| Line-ups | Yes — `GET /fixtures/lineups` |
| Top scorers (+ assists / cards lists) | Yes — `GET /players/topscorers` and related top-list endpoints |
| Players & coaches | Partly — squad `/players` per club; coach may appear on lineup payloads where the API returns it; no separate "coaches only" ingest |
| Player transfers | Yes — `GET /transfers` by team |
| Injuries | Yes — `GET /injuries` |
| Pre-match / in-play odds | Not in this repo (no odds ingest) |
| Statistics | Yes — `GET /fixtures/statistics` and fixture player stats |
| Predictions | Yes — `GET /predictions` |
| Countries | Not ingested (would be `GET /countries` if added later) |
| Head to head | Not ingested (`GET /fixtures/headtohead` if added later) |
| Live score as a separate stream | Not a separate scheduled ingest; fixture refresh covers scheduled data |
| Trophies | Not ingested |
| Sidelined | Not ingested unless mapped explicitly later |

---

## Operational tables

Support safe scheduling, not match statistics.

| Purpose | BigQuery table |
|---------|----------------|
| Single-flight ingest lock | `RAW_APIF_INGEST_LOCK` |
| Optional fanout cursor (rotating "where to continue") | `RAW_D1_APIF_INGEST_CURSOR` |

---

## Downstream

Source-near columns for D1 live under `dbt_project/models/1_staging/api_football/`. Layer conventions are documented in `dbt_project/docs/layering.md`. For commands, env vars, locks, and playbooks, see [`operations_guide.md`](operations_guide.md).
