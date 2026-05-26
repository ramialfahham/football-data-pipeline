with src as (
    select *
    from {{ apif_latest_source_partition('api_football', 'raw_apif_spl_rounds') }}
),

season_blocks as (
    select
        'SPL' as league_code,
        src.ingested_at as raw_ingested_at,
        season_block,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json
    from src,
        unnest(coalesce(json_query_array(src.payload, '$.response'), [])) as season_block
),

exploded as (
    select
        league_code,
        raw_ingested_at,
        api_errors_json,
        api_reported_result_count,
        request_parameters_json,
        round_el,
        safe_cast(json_value(season_block, '$.season') as int64) as api_season_year
    from season_blocks,
        unnest(
            case
                when json_value(season_block, '$.season') is not null
                    then coalesce(json_query_array(json_query(season_block, '$.rounds'), '$'), [])
                else array[season_block]
            end
        ) as round_el
)

select
    league_code,
    raw_ingested_at,
    api_season_year,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    coalesce(json_value(round_el, '$'), to_json_string(round_el)) as round_name,
    coalesce(json_value(round_el, '$'), to_json_string(round_el)) as source_json
from exploded
