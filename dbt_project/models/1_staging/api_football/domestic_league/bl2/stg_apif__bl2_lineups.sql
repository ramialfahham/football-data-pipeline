with src as (
    select *
    from {{ source('api_football', 'raw_apif_bl2_fixture_details') }}
),

fixtures as (
    select
        src.ingested_at as raw_ingested_at,
        fixture_json,
        'BL2' as league_code
    from src,
        unnest(coalesce(json_query_array(src.payload, '$.response'), [])) as fixture_json
),

line_rows as (
    select
        league_code,
        raw_ingested_at,
        lineup_el,
        safe_cast(json_value(fixture_json, '$.fixture.id') as int64) as fixture_id
    from fixtures,
        unnest(json_query_array(fixture_json, '$.lineups')) as lineup_el
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
    json_query(lineup_el, '$.substitutes') as substitutes_json,
    to_json_string(lineup_el) as source_json
from line_rows
