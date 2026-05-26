SELECT
    fixture_date,
    home_team_name,
    away_team_name,
    home_form_matchdays_used,
    away_form_matchdays_used,
    home_goals_for_sum_form,
    away_goals_for_sum_form,
    home_league_rank,
    away_league_rank,
    home_standings_group_description,
    away_standings_group_description
FROM `football-data-pipeline-gcp.marts.mart_matchday_insights_bl1`
ORDER BY fixture_date;
