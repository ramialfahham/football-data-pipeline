SELECT DISTINCT round_name, api_season_year
FROM `football-data-pipeline-gcp.staging.stg_apif__bl1_rounds`
WHERE api_season_year IN (2024, 2025)
    AND (LOWER(round_name) LIKE '%releg%' OR round_name = 'Final')
ORDER BY api_season_year, round_name;
