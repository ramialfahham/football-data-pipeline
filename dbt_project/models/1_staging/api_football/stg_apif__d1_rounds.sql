with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_rounds') }}
),

season_blocks as (
    select
        'D1' as league_code,
        src.ingested_datetime as raw_ingested_datetime,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json,
        season_block
    from src,
    unnest(ifnull(json_query_array(src.payload, '$.response'), [])) as season_block
),

exploded as (
    select
        league_code,
        raw_ingested_datetime,
        api_errors_json,
        api_reported_result_count,
        request_parameters_json,
        safe_cast(json_value(season_block, '$.season') as int64) as api_season_year,
        round_el
    from season_blocks,
    unnest(
        case
            when json_value(season_block, '$.season') is not null
            then ifnull(json_query_array(json_query(season_block, '$.rounds'), '$'), [])
            else array[season_block]
        end
    ) as round_el
)

select
    league_code,
    raw_ingested_datetime,
    api_season_year,
    coalesce(json_value(round_el, '$'), to_json_string(round_el)) as round_name,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    coalesce(json_value(round_el, '$'), to_json_string(round_el)) as source_json
from exploded
