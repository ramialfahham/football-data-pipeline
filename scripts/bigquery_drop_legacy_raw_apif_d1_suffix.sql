-- Drop raw tables from the old naming convention (league suffix): RAW_APIF_<ENTITY>_D1
-- Run after ingestion has populated RAW_D1_APIF_* and you no longer need legacy tables.
-- Edit project/dataset if needed (default dataset id `raw`).

drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURES_NEXT_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_LEAGUES_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_STANDINGS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_ROUNDS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_TEAMS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_INJURIES_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_TOPSCORERS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_TOPASSISTS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_TOPYELLOWCARDS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_TOPREDCARDS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_TRANSFERS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_LINEUPS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURE_EVENTS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURE_STATISTICS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_FIXTURE_PLAYERS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_PREDICTIONS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_ODDS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_PLAYERS_D1`;
drop table if exists `football-data-pipeline-gcp.raw.RAW_APIF_INGEST_CURSOR_D1`;
