SELECT DISTINCT round_name
FROM `football-data-pipeline-gcp.staging.stg_apif__bl1_rounds`
WHERE api_season_year = 2025
ORDER BY 1;
