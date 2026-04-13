with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_odds') }}
),

blocks as (
    select
        coalesce(json_value(src.payload, '$.league_code'), 'D1') as league_code,
        src.ingested_datetime as raw_ingested_datetime,
        block
    from src,
    unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as block
),

odds_rows as (
    select
        league_code,
        raw_ingested_datetime,
        safe_cast(json_value(block, '$.fixture_id') as int64) as fixture_id,
        odds_el
    from blocks,
    unnest(
        json_query_array(json_query(block, '$.odds'), '$')
    ) as odds_el
)

select
    league_code,
    raw_ingested_datetime,
    fixture_id,
    safe_cast(json_value(odds_el, '$.league.id') as int64) as odds_league_id,
    json_value(odds_el, '$.league.name') as odds_league_name,
    safe_cast(json_value(odds_el, '$.fixture.id') as int64) as odds_fixture_id,
    date(safe_cast(json_value(odds_el, '$.fixture.date') as timestamp)) as odds_fixture_date,
    json_query(odds_el, '$.bookmakers') as bookmakers_json,
    to_json_string(odds_el) as source_json
from odds_rows
