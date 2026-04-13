with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_transfers') }}
),

exploded as (
    select
        'D1' as league_code,
        src.ingested_datetime as raw_ingested_datetime,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json,
        row_json
    from src,
    unnest({{ apif_payload_response_json_strings('src') }}) as row_json
)

select
    league_code,
    raw_ingested_datetime,
    safe_cast(json_value(row_json, '$.player.id') as int64) as player_id,
    json_value(row_json, '$.player.name') as player_name,
    json_value(row_json, '$.player.photo') as player_photo_url,
    json_query(safe.parse_json(row_json), '$.transfers') as transfers_json,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    row_json as source_json
from exploded
