with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_teams') }}
),

exploded as (
    select
        'BL1' as league_code,
        src.ingested_at as raw_ingested_at,
        row_json,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json
    from src,
        unnest({{ apif_payload_response_json_strings('src') }}) as row_json
)

select
    league_code,
    raw_ingested_at,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    row_json as source_json,
    safe_cast(json_value(row_json, '$.league.season') as int64) as season,
    safe_cast(json_value(row_json, '$.team.id') as int64) as team_id,
    json_value(row_json, '$.team.name') as team_name,
    json_value(row_json, '$.team.code') as team_code,
    json_value(row_json, '$.team.country') as team_country,
    safe_cast(json_value(row_json, '$.team.founded') as int64) as founded_year,
    json_value(row_json, '$.team.logo') as team_logo_url,
    json_value(row_json, '$.venue.id') as venue_id,
    json_value(row_json, '$.venue.name') as venue_name,
    json_value(row_json, '$.venue.address') as venue_address,
    json_value(row_json, '$.venue.city') as venue_city,
    safe_cast(json_value(row_json, '$.venue.capacity') as int64) as venue_capacity
from exploded
