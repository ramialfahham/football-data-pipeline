with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_topassists') }}
),

exploded as (
    select
        'D1' as league_code,
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
    safe_cast(json_value(row_json, '$.player.id') as int64) as player_id,
    json_value(row_json, '$.player.name') as player_name,
    json_value(row_json, '$.player.photo') as player_photo_url,
    safe_cast(json_value(row_json, '$.statistics[0].team.id') as int64) as team_id,
    json_value(row_json, '$.statistics[0].team.name') as team_name,
    safe_cast(json_value(row_json, '$.statistics[0].goals.assists') as int64) as assists_total,
    safe_cast(json_value(row_json, '$.statistics[0].games.appearences') as int64) as appearances
from exploded
