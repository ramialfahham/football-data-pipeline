with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_injuries') }}
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
    safe_cast(json_value(row_json, '$.player.id') as int64) as player_id,
    json_value(row_json, '$.player.name') as player_name,
    json_value(row_json, '$.player.photo') as player_photo_url,
    safe_cast(json_value(row_json, '$.team.id') as int64) as team_id,
    json_value(row_json, '$.team.name') as team_name,
    json_value(row_json, '$.team.logo') as team_logo_url,
    safe_cast(json_value(row_json, '$.fixture.id') as int64) as fixture_id,
    json_value(row_json, '$.league.name') as injury_league_name,
    json_value(row_json, '$.league.country') as injury_league_country,
    json_value(row_json, '$.type') as injury_type,
    json_value(row_json, '$.reason') as injury_reason
from exploded
