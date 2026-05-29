with src as (
    select *
    from {{ source('api_football', 'raw_apif_fixture_details') }}
),

stats_rows as (
    select
        src.league_code,
        src.ingested_at as raw_ingested_at,
        stat_el,
        safe_cast(json_value(src.payload, '$.fixture.id') as int64) as fixture_id
    from src,
        unnest(json_query_array(src.payload, '$.statistics')) as stat_el
)

-- Faithful 1:1 flatten: one row per statistic line per team per fixture.
-- No pivot and no dedup here — both are business reshaping that belong in
-- base_apif__fixture_statistics. Staging only unnests and types the raw payload.
select
    league_code,
    raw_ingested_at,
    fixture_id,
    safe_cast(json_value(stat_el, '$.team.id') as int64) as team_id,
    json_value(stat_el, '$.team.name') as team_name,
    json_value(line_el, '$.type') as stat_type,
    json_value(line_el, '$.value') as stat_value_raw,
    to_json_string(stat_el) as source_json
from stats_rows,
    unnest(json_query_array(stat_el, '$.statistics')) as line_el
