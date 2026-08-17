# Data contract: API-Football → BigQuery

Active competitions: see `docs/competition_registry.yml` for the full list. Each competition has an internal `league_code` used as the partition key through every layer. Raw BigQuery tables are named `RAW_APIF_{entity}` (e.g. `RAW_APIF_FIXTURES_NEXT`). All competitions share the same unified raw tables, discriminated by a `league_code STRING` column — see [Unified raw tables](#unified-raw-tables) below, which is the list. The registry of active competitions lives in `docs/competition_registry.yml`.

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
| `fixture_id` | `INT64` | Present only in `RAW_APIF_FIXTURE_DETAILS` — a top-level key for per-fixture lookups, extracted from `payload` `$.fixture.id`. It is NOT a uniqueness key: the table is append-only, so a retried fixture has one row per fetch |

No `response` data is discarded at ingest, so new fields surface in modelling without refetching; the reshape loaders above drop only the per-call envelope metadata (`get`/`parameters`/`errors`/`results`/`paging`), not the response items.

Raw tables are **created** partitioned by `DATE(ingested_at)` and clustered by `league_code` (`ingestion/api_football/bigquery.py:88-93`). Two cautions go with that, and the second one has cost real money:

- Creation uses `exists_ok=True`, so a table that predates the partitioning code is **never retro-fitted**. Do not assume a given raw table is partitioned — check it: `bq show --format=prettyjson football-data-pipeline-gcp:raw.RAW_APIF_<ENTITY>` and read `timePartitioning` (metadata only, free).
- **Do not add an `ingested_at` time filter to a reader in order to "prune".** Nine biennial and quadrennial competitions go months between ingests, so any time window silently drops them — that is issue #892, and it is why partition expiry and a current/archive split were both rejected. `DATE(ingested_at)` partitioning is a write-side property; it is **not** available as a general read-side cost lever, because the only thing a reader can safely key on is `league_code`. Bounding the table by deleting at write time was tried (#33 item 8) and **reversed on 2026-08-17** — see [Raw appends and never deletes](#raw-appends-and-never-deletes). The way scan cost is actually bounded today is that staging is materialised as a **table**, so each raw table is parsed once a night rather than once per test (#33 items 9/10). If the raw tables ever need bounding again it is compaction by **version count** per key in a separate job, never a delete at write time, and never keyed on time (#892).

dbt staging reads `payload` and exposes `ingested_at` as `raw_ingested_at`.

---

## Unified raw tables

The tables below serve the entire fleet of competitions. No per-competition raw tables exist.

⚠ Deliberately no count, HERE OR ANYWHERE ELSE IN THIS FILE. This sentence said "Eleven" and went
stale the moment `RAW_APIF_INJURIES` was removed (#33 item 15) — and it was already ambiguous,
since `RAW_APIF_LEAGUES` is listed separately as "additional" and it was never clear whether it
sat inside the number. The opening paragraph carried the SAME count under the OPPOSITE convention
(eleven, only correct if `RAW_APIF_LEAGUES` IS included), so the document contradicted itself on
its own second line; a reviewer caught that when the first fix closed only one of the two.
`CLAUDE.md` gives the same instruction for the same reason ("do not quote a fixed number here; it
has been wrong before") and names the commands to recount. The table IS the count. If you add or
remove a raw table, edit the table below and nothing else.

**Every entity table is `append`. There is no other write mode**, and the "Row grain" column below
describes what one row COVERS, never a uniqueness guarantee. Since 2026-08-17 nothing in ingestion
deletes from raw.

| Table | Write mode | Partition | Cluster | Row grain (per write) |
|-------|------------|-----------|---------|-----------------------|
| `RAW_APIF_FIXTURE_DETAILS` | append | `DATE(ingested_at)` | `league_code` | one fixture |
| `RAW_APIF_FIXTURES_NEXT` | append | `DATE(ingested_at)` | `league_code` | whole league |
| `RAW_APIF_STANDINGS` | append | `DATE(ingested_at)` | `league_code` | whole league |
| `RAW_APIF_TEAMS` | append | `DATE(ingested_at)` | `league_code` | whole league |
| `RAW_APIF_PLAYERS` | append | `DATE(ingested_at)` | `league_code` | one `(team, season)` |
| `RAW_APIF_COACHES` | append | `DATE(ingested_at)` | `league_code` | whole league |
| `RAW_APIF_TRANSFERS` | append | `DATE(ingested_at)` | `league_code` | whole league |
| `RAW_APIF_SQUADS` | append | `DATE(ingested_at)` | `league_code` | team subset |
| `RAW_APIF_PLAYER_PROFILES` | append | `DATE(ingested_at)` | `league_code` | new players only |
| `RAW_APIF_PLAYER_TEAMS` | append | `DATE(ingested_at)` | `league_code` | new players only |

Additional smaller table: `RAW_APIF_LEAGUES` (same append schema, no `fixture_id`).

---

## Append-only writes (reference tables)

Reference tables — fixtures-next, coaches, leagues, squads, player-profiles, player-teams — are written with `WRITE_APPEND`. On every pipeline run:

1. The pipeline assembles the **full history window** for the competition. A full (active) run fetches every configured season from the API, reusing finished historical seasons from the previous snapshot (issue #283). A poll/idle run (a finished competition) fetches only the current season and **carries forward** the prior seasons from the latest snapshot — finished matches never change, so the carried rows stay current. Either path yields a complete response.
2. The complete response is written as a new row with the current UTC timestamp.
3. Prior rows are preserved. BigQuery retains the full ingest history.

The latest row always contains the complete picture because every run writes a **complete** snapshot (current season refreshed; finished seasons reused or carried forward). This is the invariant the full-refresh `fct_fixture` depends on, so it must hold for active **and** idle competitions. The staging models that read a per-league snapshot table keep only the latest snapshot per league, with `league_code` as the sole partitioning key of the window:

```sql
qualify row_number() over (
    partition by league_code order by ingested_at desc
) = 1
```

This is what the six per-league snapshot staging models do today — `stg_apif__fixtures_next`, `_leagues`, `_squads`, `_standings`, `_teams`, `_transfers`. The other staging models deliberately do **not** apply it: `RAW_APIF_FIXTURE_DETAILS` and `RAW_APIF_PLAYERS` are keyed BELOW `league_code` (one row per fixture, one row per `(team, season)`), so a latest-per-league window there would keep one fixture or one team-season and drop every other. Those models read all rows and base resolves the entity.

**No staging model carries a `DATE(ingested_at)` pre-filter, and none should.** This document used to prescribe a 7-day one here. No model ever implemented it, and it would have been a live defect if one had — see the second bullet under raw partitioning above (#892). Ranking cannot prune a partition, so the pre-filter bought nothing it claimed to buy.

**`RAW_APIF_PLAYERS` grain (one row per team×season per fetch).** The `/players` roster snapshot is written as **one small row per `(team, season)`** (each row's `response` carries a single `{team_id, season, players_payload}` entry), not one giant per-league row — so no single row approaches BigQuery's 100 MB per-row JSON limit for large-roster deep leagues (LIBER/UEL/UCL), which previously failed to load. Each run appends the freshly-fetched per-(team,season) rows and removes nothing, so a re-fetched key accumulates one row per fetch and the earlier version stays available to base. Because it is keyed below `league_code` (no per-league snapshot), `stg_apif__players` reads **all** rows faithfully — **no** latest-snapshot `QUALIFY` (which is also forbidden in staging for a non-`league_code` partition) — and current-per-`(player, team, season)` is assembled in **base** (`base_apif__player_team_season` / `base_apif__players` dedup by entity keys, robust to any transient duplicate). This satisfies the staging layer contract (entity deduplication belongs in base, never staging — see `dbt_project/docs/layering.md` §1_staging). The existing bloated rows are converted to this grain by the one-time `scripts/diagnostics/reshape_players_to_team_season.py` (data-preserving — verified to reproduce the exact distinct player-team-season set).

This scales cleanly: adding more seasons or competitions adds rows to existing tables, not new tables.

---

## Raw appends and never deletes

**CPO ruling, 2026-08-17: raw keeps every version the provider ever gave us. Base decides which one
wins.** No loader deletes from a raw table, for any table, under any condition. This reverses the
delete half of #539 (2026-06-22) and all of #33 item 8b (2026-08-09), knowingly and on the record.

The rule exists because "should this answer replace what we already hold" is a question ingestion
cannot answer. The only signal available at write time is `result_is_complete()`, which tests
whether the CALL failed, not whether the ANSWER shrank — and an empty error-free response counts as
complete by deliberate decision (2026-08-03), because the provider genuinely reporting no rows is
indistinguishable from it. Three deletes were built on that signal and all three destroyed data:

| Deleted mechanism | What it cost |
|---|---|
| `_delete_fixtures` (retry, per fixture) | 29 events across 5 fixtures, including a whole penalty shootout, unrecoverable |
| `_delete_superseded_player_rows` (per `(team, season)`) | 4 squads on 2026-08-02: UCL 340 went 25 players to 0 |
| `delete_superseded_league_rows` (per league) | never fired destructively that we know of; it would have wiped a competition's entire standings/teams/transfers history in one run |

The scan-cost argument that bought them is spent. `RAW_APIF_TRANSFERS` really did fall from 6.99 GiB
to 0.178 GiB under 8b, but staging became a materialised **table** four days later (#33 items 9/10),
so each raw table is now parsed once a night instead of once per test. Append-only costs roughly
$1-2/month in scanning plus cents of storage.

**Do not reintroduce a delete to bound a table.** If growth needs bounding, compact by **version
count** per key in a separate job: it prunes on the clustering key and is competition-frequency
agnostic, where a time-based rule silently drops biennial and quadrennial competitions that go
months between ingests (#892). The removal is pinned behaviourally by
`tests/test_raw_merge_on_write.py`, which asserts no loader issues DML at all.

**What did NOT change: the #896 completeness guard.** A fetch that errored or was cut short by the
quota is still discarded whole and retried next run, in `batch_fixtures`, `coaches`, `standings`,
`teams` and `squads`. Append-only makes a bad write recoverable; it is not a reason to make one.

---

## Fixture details (append-only, one row per fetch)

`RAW_APIF_FIXTURE_DETAILS` appends. Each run fetches only the fixtures that are missing data (not the full history) and appends one row per fixture returned. A fixture that is retried — empty statistics within the 3-day window from kickoff — gains a **second row**; nothing is removed.

**Both versions are kept deliberately, and base picks per entity.** The bundle carries lineups, events, statistics and player stats *together*, so a retry chasing late statistics can come back richer in one section and poorer in another. `base_apif__fixture_events` dedups newest-per-`(league_code, fixture_id, event_index)`, `base_apif__fixture_players` per `(…, team_id, player_id)`, `base_apif__fixture_statistics` per `(…, team_id)` — so an entity present only in the older payload survives, and one present in both takes the newer. On fixture 1564795 that yields 27 events: indices 0-16 from the retry, 17-26 from the payload it would have replaced.

Two consequences worth stating rather than discovering:

- `fixture_id` is **not** a uniqueness key on this table. Any reader that assumes one row per fixture must aggregate — `coverage.read_coverage` and `batch_fixtures._read_fetched_coverage` both use `LOGICAL_OR ... GROUP BY fixture_id` for exactly this reason.
- `stg_apif__lineups` has **no consumer**, so nothing downstream resolves its versions today.

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

## Fetch-side skip (ingested once → not re-requested)

**Invariant — every per-entity endpoint must skip what it already holds.** Storage-side merge/dedup bounds the *table*; it does **not** bound the *API cost*. A loader that keeps one row per key but still calls the endpoint for every key every run re-pays the full quota nightly. This reached production once: the `/players` squad phase re-fetched every team × every history season each run (~50% of the daily quota) because it had the merge but not the skip.

So any per-entity pull (per-fixture, per-team, per-team-season, per-player) MUST, before fetching, read the keys already ingested from the target raw table and fetch only the delta. The single deliberate exception is the **live/current season**, whose per-season stats keep accumulating — it is re-fetched every run; every finished season/fixture is immutable and fetched once. Mirror the canonical implementations, do not reinvent:

| Endpoint axis | Coverage reader | Fetch planner |
|---------------|-----------------|---------------|
| per-fixture (`/fixtures?ids=`) | `read_coverage` / `covered_for_league` | fanout selection (above) |
| per-team-season (`/players`) | `captured_player_team_seasons` (`loads/squads.py`) | `plan_player_team_season_fetch` |
| per-team-season (`/players/squads`) | `captured_team_seasons` (`loads/player_squads.py`) | `select_squad_catchup_team_ids` |
| per-player (`/players/profiles`, `/players/teams`) | `players_needing` (`loads/player_universe.py`) | static bio/career — fetch each player once |

Each fetch pass logs `to_fetch=N skipped_cached=M`, so a regression (skip silently disabled) shows up in the run log.

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
2. **History** — raw tables carry each competition's season depth from its `history_seasons` (registry), which is authoritative; when unset, the default window (`DEFAULT_SEASON_WINDOW_YEARS` in `ingestion/api_football/settings.py`) applies.
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

Each row is one HTTP area and the BigQuery raw table where its payload lives. Dataset id defaults to `raw`, configurable via `API_FOOTBALL_BIGQUERY_DATASET`. Every entity table uses `WRITE_APPEND` and nothing deletes — see the write-mode table above and [Raw appends and never deletes](#raw-appends-and-never-deletes). What differs between tables is only what one written row COVERS: a whole league, one fixture, or one `(team, season)`.

| Area | Endpoint(s) | BigQuery raw table |
|------|-------------|-------------------|
| Fixtures | `/fixtures` | `RAW_APIF_FIXTURES_NEXT` |
| League + coverage | `/leagues?id=` (all seasons in `seasons[]`) | `RAW_APIF_LEAGUES` |
| Standings | `/standings` | `RAW_APIF_STANDINGS` |
| Teams | `/teams` | `RAW_APIF_TEAMS` |
| Squad | `/players` per team, with `page=` merged where applicable | `RAW_APIF_PLAYERS` |
| Coaches | `/coachs` per team | `RAW_APIF_COACHES` |
| Transfers | `/transfers` per team (full move history) | `RAW_APIF_TRANSFERS` |
| Player squads | `/players/squads` per team (current squad + shirt number); captured for in-season comps every run **and** for finished comps via a team-keyed catch-up — club + national (see [Squad capture](#squad-capture-in-season--finished-comp-catch-up)) | `RAW_APIF_SQUADS` |
| Player profiles | `/players/profiles` per player (bio) | `RAW_APIF_PLAYER_PROFILES` |
| Player teams | `/players/teams` per player (career team×seasons) | `RAW_APIF_PLAYER_TEAMS` |
| Per-fixture bundle | `/fixtures/lineups`, `/fixtures/events`, `/fixtures/statistics`, `/fixtures/players` | `RAW_APIF_FIXTURE_DETAILS` (one row per fetch of a fixture; sub-endpoints stored as JSON sub-keys within `payload`) |

**Retired:** `/fixtures/rounds` → `RAW_APIF_ROUNDS` is no longer ingested. Nothing consumed the rounds endpoint — every `round_name` in the warehouse comes from the `$.league.round` field on `/fixtures`. The daily call was removed to save quota; any historical `RAW_APIF_ROUNDS` table is dormant (not written, not read). Reintroduce only if a canonical `dim_round` consumer appears.

**Reinstated 2026-06-14 (reverses #420):** `/transfers` → `RAW_APIF_TRANSFERS` is ingested again, pulled **by team** (one call returns all of that team's players' moves; a full-history snapshot appended per run, deduped downstream — by-team fetching returns each move twice, once per involved team). It feeds `fct_transfer` (dated moves), the dated source of the player **affiliation timeline** — the ordering the dateless roster mapping and lagging match-recency cannot provide. (It was retired with #420 when nothing consumed it; reinstated by CPO decision once the affiliation-order requirement made transfer dates necessary. `transfer_type` is kept as the raw provider string — no canonical taxonomy.)

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
| Injuries | **No — deliberately not ingested.** `/injuries` was ingested until 2026-08-13 and had no consumer: no source declaration, no model, no export. Removed under #33 item 15; `RAW_APIF_INJURIES` was the largest raw table at 1.975 GiB. It had been removed once before (2026-05-10) for the same reason and re-added without one. Do not re-add without a named downstream consumer. |
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
