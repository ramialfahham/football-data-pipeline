-- Drop legacy API-Football raw tables (E0, I1, SP1, F1). D1 tables are kept.
-- Project/dataset: edit if yours differ.
-- Run via BigQuery console (allow multi-statement) or: bq query --use_legacy_sql=false < scripts/bigquery_drop_non_d1_raw_tables.sql

drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_FIXTURES_NEXT_E0`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_FIXTURES_NEXT_I1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_FIXTURES_NEXT_SP1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_FIXTURES_NEXT_F1`;

drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_PLAYERS_E0`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_PLAYERS_I1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_PLAYERS_SP1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_PLAYERS_F1`;

drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_LINEUPS_E0`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_LINEUPS_I1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_LINEUPS_SP1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_LINEUPS_F1`;

drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_INJURIES_E0`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_INJURIES_I1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_INJURIES_SP1`;
drop table if exists `football-data-pipeline-gcp.API_FOOTBALL.RAW_APIF_INJURIES_F1`;
