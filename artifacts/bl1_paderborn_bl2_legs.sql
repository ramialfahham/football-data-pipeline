SELECT COUNT(*) AS bl2_finished_legs
FROM `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg`
WHERE
    league_code = 'BL2'
    AND season_api_year = 2025
    AND team_sk IN (
        SELECT team_sk
        FROM `football-data-pipeline-gcp.core.dim_team`
        WHERE team_name = 'SC Paderborn 07'
    );

SELECT
    DATE(kickoff_datetime) AS match_date,
    round_name,
    goals_for,
    goals_against
FROM `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg`
WHERE
    league_code = 'BL2'
    AND season_api_year = 2025
    AND team_sk IN (
        SELECT team_sk
        FROM `football-data-pipeline-gcp.core.dim_team`
        WHERE team_name = 'SC Paderborn 07'
    )
ORDER BY kickoff_datetime DESC
LIMIT 5;
