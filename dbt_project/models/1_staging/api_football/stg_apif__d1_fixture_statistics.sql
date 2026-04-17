with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_fixture_statistics') }}
),

blocks as (
    select
        src.ingested_at as raw_ingested_at,
        block_json,
        coalesce(json_value(src.payload, '$.league_code'), 'D1') as league_code
    from src,
        unnest(coalesce(json_query_array(src.payload, '$.response'), [])) as block_json
),

stats_rows as (
    select
        league_code,
        raw_ingested_at,
        stat_el,
        safe_cast(json_value(block_json, '$.fixture_id') as int64) as fixture_id
    from blocks,
        unnest(json_query_array(block_json, '$.statistics')) as stat_el
)

select
    league_code,
    raw_ingested_at,
    fixture_id,
    safe_cast(json_value(stat_el, '$.team.id') as int64) as team_id,
    json_value(stat_el, '$.team.name') as team_name,
    json_query(stat_el, '$.statistics') as statistics_lines_json,
    to_json_string(stat_el) as source_json
from stats_rows
