-- Drop legacy API-Football raw tables for leagues other than D1 (E0, I1, SP1, F1).
-- Covers both historical naming styles:
--   - suffix league: RAW_APIF_<ENTITY>_<LEAGUE>
--   - league-first: RAW_<LEAGUE>_APIF_<ENTITY> (matches current ingestion pattern for multi-league).
-- Project/dataset: default raw layer dataset id is `raw` (set API_FOOTBALL_BIGQUERY_DATASET in ingestion).
-- If you still use legacy dataset `API_FOOTBALL`, replace `raw` below.
-- Run via BigQuery console (allow multi-statement) or: bq query --use_legacy_sql=false < scripts/bigquery_drop_non_d1_raw_tables.sql

-- Legacy: league suffix on APIF_* (older ingestion)
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURES_NEXT_E0`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURES_NEXT_I1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURES_NEXT_SP1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURES_NEXT_F1`;

drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_PLAYERS_E0`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_PLAYERS_I1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_PLAYERS_SP1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_PLAYERS_F1`;

drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_LINEUPS_E0`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_LINEUPS_I1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_LINEUPS_SP1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_LINEUPS_F1`;

drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_INJURIES_E0`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_INJURIES_I1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_INJURIES_SP1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_INJURIES_F1`;

-- League-first (same entities; safe if tables never existed)
drop table if exists `football-data-pipeline-gcp.raw.RAW_E0_APIF_FIXTURES_NEXT`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_I1_APIF_FIXTURES_NEXT`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_SP1_APIF_FIXTURES_NEXT`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_F1_APIF_FIXTURES_NEXT`;

drop table if exists `football-data-pipeline-gcp.raw.RAW_E0_APIF_PLAYERS`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_I1_APIF_PLAYERS`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_SP1_APIF_PLAYERS`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_F1_APIF_PLAYERS`;

drop table if exists `football-data-pipeline-gcp.raw.RAW_E0_APIF_LINEUPS`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_I1_APIF_LINEUPS`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_SP1_APIF_LINEUPS`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_F1_APIF_LINEUPS`;

drop table if exists `football-data-pipeline-gcp.raw.RAW_E0_APIF_INJURIES`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_I1_APIF_INJURIES`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_SP1_APIF_INJURIES`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_F1_APIF_INJURIES`;
