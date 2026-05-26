-- Raw fallback: BL1 fixtures May-Jun 2026 from merged payload
SELECT
    JSON_VALUE(m, '$.fixture.date') AS kickoff,
    JSON_VALUE(m, '$.league.round') AS round_name,
    JSON_VALUE(m, '$.fixture.status.short') AS status_short,
    JSON_VALUE(m, '$.teams.home.name') AS home_team,
    JSON_VALUE(m, '$.teams.away.name') AS away_team,
    CAST(JSON_VALUE(m, '$.league.season') AS INT64) AS season,
    CAST(JSON_VALUE(m, '$.league.id') AS INT64) AS league_api_id
FROM `football-data-pipeline-gcp.raw.RAW_APIF_BL1_FIXTURES_NEXT`,
    UNNEST(JSON_QUERY_ARRAY(payload, '$.response')) AS m
WHERE
    CAST(JSON_VALUE(m, '$.league.season') AS INT64) IN (2024, 2025)
    AND DATE(SAFE_CAST(JSON_VALUE(m, '$.fixture.date') AS TIMESTAMP))
    BETWEEN '2026-05-01' AND '2026-06-15'
ORDER BY 1;
