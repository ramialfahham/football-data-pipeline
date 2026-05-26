SELECT COUNT(*) AS mart_rows
FROM `football-data-pipeline-gcp.marts.mart_matchday_insights_bl1`;

SELECT fixture_date, round_name, home_team_name, away_team_name
FROM `football-data-pipeline-gcp.marts.mart_matchday_insights_bl1`
ORDER BY fixture_date;
