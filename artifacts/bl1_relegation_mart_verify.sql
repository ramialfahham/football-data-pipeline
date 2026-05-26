SELECT
    fixture_date,
    home_team_name,
    away_team_name,
    home_form_league_code,
    away_form_league_code,
    home_form_matchdays_used,
    away_form_matchdays_used,
    home_goals_for_sum_form,
    away_goals_for_sum_form,
    home_league_rank,
    away_league_rank
FROM `football-data-pipeline-gcp.marts.mart_matchday_insights_bl1_relegation`
ORDER BY fixture_date;
