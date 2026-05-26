SELECT
    team_name,
    standing_rank,
    group_description
FROM `football-data-pipeline-gcp.core.fct_standings` AS s
JOIN `football-data-pipeline-gcp.core.dim_team` AS t
    ON s.team_sk = t.team_sk
WHERE
    s.league_code = 'BL1'
    AND s.season_api_year = 2025
    AND (
        LOWER(group_description) LIKE '%releg%'
        OR LOWER(group_description) LIKE '%promotion%'
        OR team_name IN ('VfL Wolfsburg', 'SC Paderborn 07')
    )
ORDER BY standing_rank;
