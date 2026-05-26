SELECT
    f.fixture_date,
    f.round_name,
    f.status_short,
    ht.team_name AS home_team_name,
    at.team_name AS away_team_name,
    f.league_sk AS league_api_id,
    f.season_api_year
FROM `football-data-pipeline-gcp.core.fct_fixture` AS f
LEFT JOIN `football-data-pipeline-gcp.core.dim_team` AS ht
    ON f.home_team_sk = ht.team_sk
LEFT JOIN `football-data-pipeline-gcp.core.dim_team` AS at
    ON f.away_team_sk = at.team_sk
WHERE
    f.league_code = 'BL2'
    AND f.fixture_date BETWEEN '2026-05-01' AND '2026-06-15'
ORDER BY f.fixture_date;
