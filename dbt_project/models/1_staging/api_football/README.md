# API-Football staging (`1_staging/api_football`)

Staging models here are **generic and competition-agnostic**. Every model reads
from a **unified `RAW_APIF_*` raw table** that holds all onboarded competitions in
one place, discriminated by a `league_code STRING` column. There are **no
per-competition staging files** — adding a league is a registry-only change (see
the zero-file rule in [`CLAUDE.md`](../../../../CLAUDE.md) and
[`docs/competition_registry.yml`](../../../../docs/competition_registry.yml)).

**Staging contract** (see [`../../docs/layering.md`](../../docs/layering.md) §1_staging):
select the latest ingestion snapshot per `league_code` (the append-log raw tables
hold one complete snapshot row per run), then faithfully flatten the payload 1:1
(rename, cast, unnest). No entity-grain deduplication, no aggregation/pivot, and no
cross-source joins — all of that is business logic that belongs in `2_base`.

Tests and column docs live in [`stg_apif__generic.yml`](stg_apif__generic.yml)
(one YAML file, many models). Each model carries **`raw_ingested_at`** (UTC load
time from the raw column **`ingested_at`**).

| dbt source (`identifier`) | Staging model(s) |
|---------------------------|------------------|
| `raw_apif_fixtures_next` (`RAW_APIF_FIXTURES_NEXT`) | [`stg_apif__fixtures_next.sql`](stg_apif__fixtures_next.sql) |
| `raw_apif_leagues` (`RAW_APIF_LEAGUES`) | [`stg_apif__leagues.sql`](stg_apif__leagues.sql) |
| `raw_apif_standings` (`RAW_APIF_STANDINGS`) | [`stg_apif__standings.sql`](stg_apif__standings.sql) |
| `raw_apif_teams` (`RAW_APIF_TEAMS`) | [`stg_apif__teams.sql`](stg_apif__teams.sql) |
| `raw_apif_players` (`RAW_APIF_PLAYERS`) | [`stg_apif__players.sql`](stg_apif__players.sql) |
| `raw_apif_fixture_details` (`RAW_APIF_FIXTURE_DETAILS`) | [`stg_apif__fixture_events.sql`](stg_apif__fixture_events.sql), [`stg_apif__fixture_players.sql`](stg_apif__fixture_players.sql), [`stg_apif__fixture_statistics.sql`](stg_apif__fixture_statistics.sql), [`stg_apif__lineups.sql`](stg_apif__lineups.sql) |

The four fixture-detail models all flatten different arrays out of the single
`RAW_APIF_FIXTURE_DETAILS` payload (`$.events`, `$.players`, `$.statistics`,
`$.lineups`).

Operational raw tables (lock, fanout cursor) are **not** in `sources.yml` and have
**no** staging models here — see [`docs/data_contract.md`](../../../../docs/data_contract.md).
