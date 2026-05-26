SELECT
    fixture_date,
    round_name,
    status_short,
    home_team_name,
    away_team_name,
    season_api_year,
    upcoming_matchday_fixture_count
FROM `football-data-pipeline-gcp.marts.mart_matchday_insights_bl1`
WHERE fixture_date >= '2026-05-01'
ORDER BY fixture_date;
