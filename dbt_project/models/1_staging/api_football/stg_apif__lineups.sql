-- RAW_APIF_FIXTURE_DETAILS is APPEND-ONLY and holds one row per FETCH of a fixture: the loader
-- skip-fetches only finished fixtures missing data, and a retry appends a second version rather
-- than replacing the first (ingestion/api_football/loads/batch_fixtures.py: raw keeps both
-- versions). So it carries many fixtures per league_code AND several versions per
-- fixture. Staging reads ALL rows faithfully (NO latest-snapshot qualify — that would drop
-- fixtures) and base assembles current-per-entity by entity-key dedup on raw_ingested_at desc.
-- ⚠ This model has NO consumer today (`dbt ls --select stg_apif__lineups+` returns only itself),
-- so nothing downstream resolves its versions. See dbt_project/docs/layering.md §1_staging.
with src as (
    select *
    from {{ source('api_football', 'raw_apif_fixture_details') }}
),

line_rows as (
    select
        src.league_code,
        src.ingested_at as raw_ingested_at,
        lineup_el,
        safe_cast(json_value(src.payload, '$.fixture.id') as int64) as fixture_id
    from src,
        unnest(json_query_array(src.payload, '$.lineups')) as lineup_el
)

select
    league_code,
    raw_ingested_at,
    fixture_id,
    safe_cast(json_value(lineup_el, '$.team.id') as int64) as team_id,
    json_value(lineup_el, '$.team.name') as team_name,
    json_value(lineup_el, '$.formation') as formation,
    json_value(lineup_el, '$.coach.name') as coach_name,
    json_query(lineup_el, '$.startXI') as start_xi_json,
    json_query(lineup_el, '$.substitutes') as substitutes_json
from line_rows
