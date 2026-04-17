# API-Football D1 staging (`1_staging/api_football`)

There are **17** staging SQL models here: **one `stg_apif__d1_*.sql` per `RAW_D1_APIF_*` raw table** declared in [`sources.yml`](sources.yml). If your editor shows fewer files, refresh the folder, confirm you are on the latest `main`, and run `git status` in this path.

Tests and column docs for these models live mainly in [`stg_apif__per_competition.yml`](stg_apif__per_competition.yml) (one YAML file, many models). Each model carries **`raw_ingested_at`** (UTC load time from raw column **`ingested_at`**).

| # | BigQuery table (`identifier`) | dbt source name | Staging model |
|---|-------------------------------|-----------------|---------------|
| 1 | `RAW_D1_APIF_FIXTURES_NEXT` | `raw_d1_apif_fixtures_next` | [`stg_apif__d1_fixtures_next.sql`](stg_apif__d1_fixtures_next.sql) |
| 2 | `RAW_D1_APIF_LEAGUES` | `raw_d1_apif_leagues` | [`stg_apif__d1_leagues.sql`](stg_apif__d1_leagues.sql) |
| 3 | `RAW_D1_APIF_STANDINGS` | `raw_d1_apif_standings` | [`stg_apif__d1_standings.sql`](stg_apif__d1_standings.sql) |
| 4 | `RAW_D1_APIF_ROUNDS` | `raw_d1_apif_rounds` | [`stg_apif__d1_rounds.sql`](stg_apif__d1_rounds.sql) |
| 5 | `RAW_D1_APIF_TEAMS` | `raw_d1_apif_teams` | [`stg_apif__d1_teams.sql`](stg_apif__d1_teams.sql) |
| 6 | `RAW_D1_APIF_INJURIES` | `raw_d1_apif_injuries` | [`stg_apif__d1_injuries.sql`](stg_apif__d1_injuries.sql) |
| 7 | `RAW_D1_APIF_TOPSCORERS` | `raw_d1_apif_topscorers` | [`stg_apif__d1_topscorers.sql`](stg_apif__d1_topscorers.sql) |
| 8 | `RAW_D1_APIF_TOPASSISTS` | `raw_d1_apif_topassists` | [`stg_apif__d1_topassists.sql`](stg_apif__d1_topassists.sql) |
| 9 | `RAW_D1_APIF_TOPYELLOWCARDS` | `raw_d1_apif_topyellowcards` | [`stg_apif__d1_topyellowcards.sql`](stg_apif__d1_topyellowcards.sql) |
| 10 | `RAW_D1_APIF_TOPREDCARDS` | `raw_d1_apif_topredcards` | [`stg_apif__d1_topredcards.sql`](stg_apif__d1_topredcards.sql) |
| 11 | `RAW_D1_APIF_TRANSFERS` | `raw_d1_apif_transfers` | [`stg_apif__d1_transfers.sql`](stg_apif__d1_transfers.sql) |
| 12 | `RAW_D1_APIF_LINEUPS` | `raw_d1_apif_lineups` | [`stg_apif__d1_lineups.sql`](stg_apif__d1_lineups.sql) |
| 13 | `RAW_D1_APIF_FIXTURE_EVENTS` | `raw_d1_apif_fixture_events` | [`stg_apif__d1_fixture_events.sql`](stg_apif__d1_fixture_events.sql) |
| 14 | `RAW_D1_APIF_FIXTURE_STATISTICS` | `raw_d1_apif_fixture_statistics` | [`stg_apif__d1_fixture_statistics.sql`](stg_apif__d1_fixture_statistics.sql) |
| 15 | `RAW_D1_APIF_FIXTURE_PLAYERS` | `raw_d1_apif_fixture_players` | [`stg_apif__d1_fixture_players.sql`](stg_apif__d1_fixture_players.sql) |
| 16 | `RAW_D1_APIF_PREDICTIONS` | `raw_d1_apif_predictions` | [`stg_apif__d1_predictions.sql`](stg_apif__d1_predictions.sql) |
| 17 | `RAW_D1_APIF_PLAYERS` | `raw_d1_apif_players` | [`stg_apif__d1_players.sql`](stg_apif__d1_players.sql) |

Operational raw tables (lock, fanout cursor) are **not** in `sources.yml` and have **no** staging models here—see [`docs/data_contract.md`](../../../../docs/data_contract.md).
