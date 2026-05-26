SELECT
    m.fixture_date,
    m.home_team_name,
    m.away_team_name,
    m.home_form_games_in_window,
    m.away_form_games_in_window,
    m.home_form_source_season_api_year,
    m.away_form_source_season_api_year,
    m.home_league_rank,
    m.away_league_rank,
    m.home_standings_group_description,
    m.away_standings_group_description
FROM `football-data-pipeline-gcp.marts.mart_matchday_insights_bl1` AS m
ORDER BY m.fixture_date;
