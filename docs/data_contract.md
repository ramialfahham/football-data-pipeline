# Data contract: API-Football → BigQuery

Active competitions: see `docs/competition_registry.yml` for the full list. Each competition has an internal `league_code` used as the partition key through every layer. Raw BigQuery tables are named `RAW_APIF_{entity}` (e.g. `RAW_APIF_FIXTURES_NEXT`). All competitions share the same eleven raw tables, discriminated by a `league_code STRING` column. The registry of active competitions lives in `docs/competition_registry.yml`.

API references:

- [API-Football v3 documentation](https://www.api-football.com/documentation-v3)
- [API-Football beginner's guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide)

---

## Landing zone

Each API-Football endpoint returns a JSON envelope: `get`, `parameters`, `errors`, `results`, `paging`, and a `response` array. The landing zone stores the response data, but loaders that batch multiple calls (per team, per season, or paged) do not keep each raw envelope as-is: most concatenate the calls' `response` arrays into one standard envelope (recomputing `results`/`paging`), while the per-team loaders for **players/squads**, **coaches**, and **transfers** store a reshaped `{league_code, response: [...]}` payload without the envelope metadata (each `response` item is itself wrapped — `{team_id, coach}` for coaches, `{team_id, season, players_payload}` for players/squads, `{team_id, transfers_payload}` for transfers). The per-item `response` data is preserved in every case. Every raw table holds:

| Column | Type | Notes |
|--------|------|-------|
| `league_code` | `STRING` | Competition identifier — the cross-cutting key shared by every layer above staging |
| `payload` | `JSON` | API-Football response data — merged into the envelope across calls, or reshaped to `{league_code, response: [...]}` for players/squads + coaches (squads also carries a `season` stamp; see the Landing-zone note above) |
| `ingested_at` | `TIMESTAMP` | UTC timestamp of the ingest run |
| `fixture_id` | `INT64` | Present only in `RAW_APIF_FIXTURE_DETAILS` — enables merge-on-write keyed on `(league_code, fixture_id)` |

No `response` data is discarded at ingest, so new fields surface in modelling without refetching; the reshape loaders above drop only the per-call envelope metadata (`get`/`parameters`/`errors`/`results`/`paging`), not the response items.

All raw tables are partitioned by `DATE(ingested_at)` and clustered by `league_code`. Queries that filter on both `league_code` and `ingested_at` read only the relevant league's data within the relevant partition, keeping scan costs low as the table grows across seasons and competitions.

dbt staging reads `payload` and exposes `ingested_at` as `raw_ingested_at`.

---

## Unified raw tables

Eleven tables serve the entire fleet of competitions. No per-competition raw tables exist.

| Table | Write mode | Partition | Cluster | Merge key |
|-------|------------|-----------|---------|-----------|
| `RAW_APIF_FIXTURE_DETAILS` | merge-on-write | `DATE(ingested_at)` | `league_code` | `(league_code, fixture_id)` |
| `RAW_APIF_FIXTURES_NEXT` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_STANDINGS` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_TEAMS` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_PLAYERS` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_COACHES` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_INJURIES` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_TRANSFERS` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_SQUADS` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_PLAYER_PROFILES` | append | `DATE(ingested_at)` | `league_code` | — |
| `RAW_APIF_PLAYER_TEAMS` | append | `DATE(ingested_at)` | `league_code` | — |

Additional smaller table: `RAW_APIF_LEAGUES` (same append schema, no `fixture_id`).

---

## Append-only writes (reference tables)

Reference tables — fixtures-next, standings, teams, players, coaches, injuries, leagues — are written with `WRITE_APPEND`. On every pipeline run:

1. The pipeline calls the API for all configured seasons (the full history window).
2. The complete response is written as a new row with the current UTC timestamp.
3. Prior rows are preserved. BigQuery retains the full ingest history.

The latest row always contains the complete picture because each run fetches all seasons from the API. Staging reads only the latest snapshot per league using partition pruning and a `QUALIFY` window:

```sql
-- Pre-filter engages partition pruning; QUALIFY picks latest snapshot per league
where DATE(ingested_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
qualify row_number() over (
    partition by league_code order by ingested_at desc
) = 1
```

This scales cleanly: adding more seasons or competitions adds rows to existing tables, not new tables.

---

## Fixture details (merge-on-write)

`RAW_APIF_FIXTURE_DETAILS` uses merge-on-write. Each run fetches only the fixtures that are missing data (not the full history), then upserts into the unified table keyed on `(league_code, fixture_id)`. The table always holds the latest payload per fixture, without accumulating duplicate rows.

The per-fixture bundle stored in `payload` covers: lineups, events, fixture statistics, and fixture player stats — all sub-keyed within the JSON envelope.

Legacy per-competition tables (`RAW_APIF_{league_code}_*`) were dropped after migration to the unified table. The only remaining per-competition operational tables are `RAW_APIF_{league_code}_INGEST_CURSOR` (pipeline state, not data — intentionally not unified).

---

## Fanout selection (completeness-driven)

`RAW_APIF_FIXTURE_DETAILS` is written fixture by fixture. Before each per-fixture pass, the loader reads the current merged payloads and extracts the set of fixture ids already covered, per endpoint, per `league_code`. Only fixtures where at least one endpoint is still missing enter the ordering and budget math. Inside the loop, each individual endpoint call is skipped when that fixture id is already covered for that endpoint.

A start-of-phase log line reports what the run will attempt:

```
[api-football] fanout_selection league=BL1 target=3074 already_complete=1501 missing_any_endpoint=1573
```

Coverage advances monotonically across runs under any ordering (`upcoming`, `cursor`, `chrono`). Once every in-scope fixture is covered across all endpoints, the fanout pass is a no-op.

---

## Squad capture (in-season + finished-comp catch-up)

`/players/squads` is the squad-**membership** source (the full current roster, including selected players with no minutes) for **clubs and national teams alike**. A squad is a property of the **team**, not the competition, so capture is keyed by team and deduped across competitions:

1. **In-season (Phase 3b)** — competitions running full phases (`upcoming_fixtures`) capture their teams' squads every run.
2. **Finished-comp catch-up (Phase 3c)** — competitions that have finished (`poll` / `idle_complete`) skip the per-team phases, so their teams are caught up here: for each finished comp's teams, capture the squad once if the team is **not** active in any full-mode comp this run and **not** already stored for that comp's last-recorded season. Deduped across comps (a club in a finished league + a finished cup is fetched once). Team lists come from the latest-season fixtures already fetched in the poll phase — no extra fixture calls. The catch-up row is written **complete per competition**: if quota is exhausted mid-competition the partial is discarded and the whole comp re-captures next run, so `stg_apif__squads` (latest snapshot per `league_code`) never selects a partial finished-comp snapshot. (In-season Phase 3b re-fetches whole every run, so its partials self-heal.)

Each snapshot is stamped with the team's last-recorded `season` (payload key `season`), so per-season coverage is exact and re-capture is avoided. The endpoint is current-only, so historical per-edition membership is **not** reconstructable from it (parked — see issue #477); the appearance fact (`fct_player_team_season`) is a complementary playing-time layer, never the roster.

---

## Data completeness

Data is complete when four conditions hold:

1. **Coverage** — every in-scope raw table has been refreshed, and staging has been rebuilt on top of that refresh.
2. **History** — raw tables carry the multi-season window configured via `V1_SEASON_WINDOW_YEARS` in `ingestion/api_football/settings.py`.
3. **Freshness** — when new source data appears (matchdays, results), the next run merges it into the corresponding raw tables.
4. **Query truth** — queries against raw or staging reflect the latest successful run, not a partial update in flight.

Heavy per-match coverage typically takes several runs under daily API limits; that is expected behaviour, not an outage. Each check below answers one of the four conditions:

| Question | Mechanism |
|----------|-----------|
| Did each raw table load recently? | dbt source freshness on `ingested_at` in `dbt_project/models/1_staging/api_football/sources.yml`. |
| Are raw tables' latest loads aligned with each other? | dbt model `int_pipeline__raw_ingestion_spread` (max `ingested_at` per table, `spread_minutes`). |
| Does staging reflect the latest raw? | Run `dbt build` for staging after a successful ingest. |
| Do per-match tables cover every finished fixture in the merged list? | Post-ingest check in `ingestion/api_football/completeness.py`, logged as `ingest_completeness_json`. Expected is restricted to fixtures with `status.short` in `FT`, `AET`, `PEN` (configured as `FINISHED_STATUS_SHORT`); unplayed fixtures are reported as `fixture_unplayed_count` but do not fail the check. The field `match_level_tables_cover_all_fixtures` is the boolean result. |

Operational detail (locks, exit codes, env vars) lives in [`operations_guide.md`](operations_guide.md).

---

## Endpoints and raw tables

Each row is one HTTP area and the BigQuery raw table where its payload lives. Dataset id defaults to `raw`, configurable via `API_FOOTBALL_BIGQUERY_DATASET`. Reference tables use `WRITE_APPEND`; `RAW_APIF_FIXTURE_DETAILS` uses merge-on-write.

| Area | Endpoint(s) | BigQuery raw table |
|------|-------------|-------------------|
| Fixtures | `/fixtures` | `RAW_APIF_FIXTURES_NEXT` |
| League + coverage | `/leagues?id=` (all seasons in `seasons[]`) | `RAW_APIF_LEAGUES` |
| Standings | `/standings` | `RAW_APIF_STANDINGS` |
| Teams | `/teams` | `RAW_APIF_TEAMS` |
| Squad | `/players` per team, with `page=` merged where applicable | `RAW_APIF_PLAYERS` |
| Injuries | `/injuries` per league per season | `RAW_APIF_INJURIES` |
| Coaches | `/coachs` per team | `RAW_APIF_COACHES` |
| Transfers | `/transfers` per team (full move history) | `RAW_APIF_TRANSFERS` |
| Player squads | `/players/squads` per team (current squad + shirt number); captured for in-season comps every run **and** for finished comps via a team-keyed catch-up — club + national (see [Squad capture](#squad-capture-in-season--finished-comp-catch-up)) | `RAW_APIF_SQUADS` |
| Player profiles | `/players/profiles` per player (bio) | `RAW_APIF_PLAYER_PROFILES` |
| Player teams | `/players/teams` per player (career team×seasons) | `RAW_APIF_PLAYER_TEAMS` |
| Per-fixture bundle | `/fixtures/lineups`, `/fixtures/events`, `/fixtures/statistics`, `/fixtures/players` | `RAW_APIF_FIXTURE_DETAILS` (one row per fixture; sub-endpoints stored as JSON sub-keys within `payload`) |

**Retired:** `/fixtures/rounds` → `RAW_APIF_ROUNDS` is no longer ingested. Nothing consumed the rounds endpoint — every `round_name` in the warehouse comes from the `$.league.round` field on `/fixtures`. The daily call was removed to save quota; any historical `RAW_APIF_ROUNDS` table is dormant (not written, not read). Reintroduce only if a canonical `dim_round` consumer appears.

**Reinstated 2026-06-14 (reverses #420):** `/transfers` → `RAW_APIF_TRANSFERS` is ingested again, pulled **by team** (one call returns all of that team's players' moves; an append-only full-history snapshot per run, deduped downstream — by-team fetching returns each move twice, once per involved team). It feeds `fct_transfer` (dated moves), the dated source of the player **affiliation timeline** — the ordering the dateless roster mapping and lagging match-recency cannot provide. (It was retired with #420 when nothing consumed it; reinstated by CPO decision once the affiliation-order requirement made transfer dates necessary. `transfer_type` is kept as the raw provider string — no canonical taxonomy.)

**Added 2026-06-15 (player-data initiative, PR-a):** three player endpoints. `/players/squads` per team → `RAW_APIF_SQUADS` (present-day squad + shirt number; distinct from the `/players` roster pull that lands `RAW_APIF_PLAYERS`). `/players/profiles` per player → `RAW_APIF_PLAYER_PROFILES` (bio) and `/players/teams` per player → `RAW_APIF_PLAYER_TEAMS` (career team×seasons) run as a **global per-player phase** over the current universe (players rostered in season ≥ `API_FOOTBALL_PLAYER_UNIVERSE_MIN_SEASON`, default 2025), derived from `RAW_APIF_PLAYERS`. Each player is grouped under a deterministic provenance `league_code` (MIN over the leagues that surfaced them — provenance, not identity, as with transfers). Already-ingested players are skipped (bio/career are static/slow-moving), so the first run is the quota-guarded backfill and later runs fetch only newly-rostered players. CPO scope ruling (2026-06-15): profiles + teams + squads; `/players/seasons` was evaluated and **not** ingested (a bare list of years, redundant with `/players/teams`).

### /fixtures query style

Default is `season` (`league` + `season` only). Alternative modes `from_to` and `next` exist for other use cases; `next` typically requires a paid plan. Fixture paging (`page=`) is only sent when `API_FOOTBALL_FIXTURE_USE_PAGE=1`, because many plans reject it.

### Pagination

`page=` is merged for `/players` when the API paginates. It is not sent on `/fixtures`, `/teams`, `/standings`, or `/transfers`, because those endpoints reject paging with `"The Page field do not exist."` and return empty when it is sent (a single `team=` call returns a team's full transfer history — verified). Opt in for `/fixtures` with `API_FOOTBALL_FIXTURE_USE_PAGE=1` only when the key is known to support it.

The keyed player endpoints `/players/squads?team=`, `/players/profiles?player=`, and `/players/teams?player=` are also fetched un-paged (`paginate=False`): each keyed query returns a single page (verified 2026-06-15 — `paging.total=1`). (The page-keyed `/players/profiles` *directory* form does paginate, but we fetch bios per player, not via the directory.)

### Coverage flags

`/leagues` exposes `coverage` flags per season. When a flag says the API does not provide a resource for that season (standings, per-fixture events, etc.), ingestion skips the corresponding calls instead of spending quota on guaranteed-empty responses. See the beginner's guide for envelope and flag behaviour.

---

## Plan vs product

Mapping from a typical API-Football subscription list to what this repository ingests today.

| Your plan often includes | In this repo today |
|--------------------------|-------------------|
| Leagues, seasons (via league payload) | Yes — `GET /leagues`, seasons in `RAW_APIF_LEAGUES` |
| Standings, teams, fixtures | Yes |
| Events | Yes — `GET /fixtures/events` (stored in `RAW_APIF_FIXTURE_DETAILS`) |
| Line-ups | Yes — `GET /fixtures/lineups` (stored in `RAW_APIF_FIXTURE_DETAILS`) |
| Top scorers (+ assists / cards lists) | Derived downstream (from `fct_fixture_player_stats` and `fct_fixture_event`); the `/players/top*` endpoints are no longer ingested |
| Players & coaches | Yes — squad `/players` per club (`RAW_APIF_PLAYERS`) and a separate per-team coaches ingest via `GET /coachs` (`RAW_APIF_COACHES`) |
| Player bio, squads, career | Yes — `/players/profiles` per player (`RAW_APIF_PLAYER_PROFILES`), `/players/squads` per team (`RAW_APIF_SQUADS`), `/players/teams` per player (`RAW_APIF_PLAYER_TEAMS`); see the player-data note above |
| Injuries | Yes — `GET /injuries` per league/season (`RAW_APIF_INJURIES`) |
| Player transfers | Yes — `/transfers` per team (`RAW_APIF_TRANSFERS`); dated moves feed `fct_transfer`, the affiliation-timeline source (reinstated 2026-06-14, see note above) |
| Pre-match / in-play odds | Not in this repo (no odds ingest) |
| Statistics | Yes — `GET /fixtures/statistics` and fixture player stats (stored in `RAW_APIF_FIXTURE_DETAILS`) |
| Predictions | Removed in PR #237 — not ingested |
| Countries | Not ingested (would be `GET /countries` if added later) |
| Head to head | Not ingested (`GET /fixtures/headtohead` if added later) |
| Live score as a separate stream | Not a separate scheduled ingest; fixture refresh covers scheduled data |
| Trophies | Not ingested |
| Sidelined | Not ingested unless mapped explicitly later |

---

## WC team market value snapshots (manual / seed)

Published-style **national-team squad market value** estimates (whole EUR) are not provided by API-Football. They are loaded from the dbt seed `wc_team_market_value_snapshot` (columns: `team_sk`, `as_of_date`, `market_value_eur`, `source_code`, `prompt_version`), typically updated twice monthly after external research. `team_sk` is the API-Football national team id (same as `dim_team.team_sk` for `league_code = 'WC'`).

Downstream: `fct_team_market_value_snapshot` → `int_team__market_value_latest` → `mart_team_market_value` (metric `market_value_eur`). Fixture-level export columns on `mart_matchday_insights_wc` are joined in a separate change. Automated ingest (e.g. LLM-assisted) may replace the seed later; raw table naming will follow `RAW_{source}_{entity}` when added.

---

## Operational tables

Support safe scheduling, not match statistics.

| Purpose | BigQuery table |
|---------|----------------|
| Single-flight ingest lock | `RAW_APIF_INGEST_LOCK` |
| Optional fanout cursor (rotating "where to continue") | `RAW_APIF_{league_code}_INGEST_CURSOR` |

---

## Downstream

Staging models live under `dbt_project/models/1_staging/api_football/` and are named `stg_apif__{entity}` (e.g. `stg_apif__fixtures_next`, `stg_apif__fixture_details`). Each generic model reads from the corresponding unified raw table and exposes `league_code` as a pass-through column. No per-competition staging files exist. Layer conventions are documented in `dbt_project/docs/layering.md`. For commands, env vars, locks, and playbooks, see [`operations_guide.md`](operations_guide.md).

---

## Adding a new competition

Every layer is competition-aware: ingestion loops over the competition registry, and the `league_code` column flows through every raw table and dbt layer. Adding a competition requires **zero file edits of any kind** — only a registry entry:

1. **Register the competition.** Add an entry to `docs/competition_registry.yml` with the `league_code`, `provider_league_id`, display name, `competition_type`, season window, and cost flags (`ingest_active`, `history_seasons`). This is the entire change — the ingestion loader reads the registry at startup, writes to the shared unified raw tables with `league_code` populated, and generic staging models surface the new `league_code` automatically.
2. **Run `python scripts/sync_dbt_vars.py`** to update `active_competition_league_codes` in `dbt_project.yml` — required only for CI checks that verify registry/var sync.
3. **Push** — CI ingests the new league into the unified tables; all downstream models (base, core, marts) pick it up via the `league_code` column.

No new staging files, no new `sources.yml` blocks, no base model edits.
