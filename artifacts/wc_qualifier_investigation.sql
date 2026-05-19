-- WC qualifier leg investigation (2026-05-19). Do not commit query results.
-- Root cause: int_wc__pre_tournament_qualifier_legs included all historical WCQ seasons.
-- Fix: wc_supporting_league_codes.qualifier_season_api_year per confederation current_season.

SELECT
    team_name,
    qualifier_games_played,
    season_api_year
FROM `football-data-pipeline-gcp.marts.mart_wc_pre_tournament_insights`
WHERE team_name IN ('Algeria', 'Morocco', 'Senegal', 'Germany', 'France', 'Argentina')
ORDER BY qualifier_games_played DESC;

SELECT
    t.team_name,
    leg.league_code,
    leg.season_api_year,
    COUNT(*) AS leg_count
FROM `football-data-pipeline-gcp.intermediate.int_wc__pre_tournament_qualifier_legs` AS leg
INNER JOIN `football-data-pipeline-gcp.core.dim_team` AS t
    ON leg.team_sk = t.team_sk
WHERE t.team_name = 'Algeria'
GROUP BY 1, 2, 3
ORDER BY leg_count DESC;
