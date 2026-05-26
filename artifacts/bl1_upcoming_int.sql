SELECT
    fixture_date,
    round_name,
    home_team_name,
    away_team_name,
    season_api_year,
    upcoming_matchday_fixture_count
FROM `football-data-pipeline-gcp.intermediate.int_matchday__upcoming_round_fixtures`
WHERE league_code = 'BL1'
ORDER BY fixture_date;
