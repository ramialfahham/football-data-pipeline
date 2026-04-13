with src as (
    select *
    from {{ source('api_football', 'raw_apif_ref_odds_bets') }}
),

exploded as (
    select
        src.ingested_datetime as raw_ingested_datetime,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json,
        row_json
    from src,
    unnest({{ apif_payload_response_json_strings('src') }}) as row_json
)

select
    raw_ingested_datetime,
    safe_cast(json_value(row_json, '$.id') as int64) as bet_id,
    json_value(row_json, '$.name') as bet_name,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    row_json as source_json
from exploded
