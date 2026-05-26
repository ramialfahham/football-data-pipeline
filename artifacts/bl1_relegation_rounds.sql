-- Query B: BL1 round names containing relegation/playoff
SELECT DISTINCT round_name
FROM `football-data-pipeline-gcp.staging.stg_apif__bl1_rounds`
WHERE
    api_season_year IN (2024, 2025)
    AND (
        LOWER(round_name) LIKE '%releg%'
        OR LOWER(round_name) LIKE '%play%'
    )
ORDER BY 1;
