-- Drop D1 raw tables that must match loader contract: payload (JSON) + ingested_datetime (TIMESTAMP).
-- After drop, run: python -m ingestion.api_football.main (when quota allows) to recreate.
-- Edit project/dataset if yours differ from defaults.

DROP TABLE IF EXISTS `football-data-pipeline-gcp.raw.RAW_D1_APIF_LINEUPS`;
DROP TABLE IF EXISTS `football-data-pipeline-gcp.raw.RAW_D1_APIF_FIXTURE_EVENTS`;
DROP TABLE IF EXISTS `football-data-pipeline-gcp.raw.RAW_D1_APIF_FIXTURE_STATISTICS`;
DROP TABLE IF EXISTS `football-data-pipeline-gcp.raw.RAW_D1_APIF_FIXTURE_PLAYERS`;
DROP TABLE IF EXISTS `football-data-pipeline-gcp.raw.RAW_D1_APIF_PREDICTIONS`;
DROP TABLE IF EXISTS `football-data-pipeline-gcp.raw.RAW_D1_APIF_PLAYERS`;
