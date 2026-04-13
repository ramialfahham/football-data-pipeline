with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_rounds') }}
),

exploded as (
    select
        'D1' as league_code,
        src.ingested_datetime as raw_ingested_datetime,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json,
        round_el
    from src,
    unnest(ifnull(json_query_array(src.payload, '$.response'), [])) as round_el
)

select
    league_code,
    raw_ingested_datetime,
    coalesce(json_value(round_el, '$'), to_json_string(round_el)) as round_name,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    coalesce(json_value(round_el, '$'), to_json_string(round_el)) as source_json
from exploded
