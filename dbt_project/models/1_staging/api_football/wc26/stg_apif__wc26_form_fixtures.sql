with src as (
    select *
    from {{ source('api_football', 'raw_wc26_apif_form_fixtures') }}
),

team_blocks as (
    select
        'WC26' as league_code,
        src.ingested_at as raw_ingested_at,
        safe_cast(json_value(block_json, '$.team_id') as int64) as queried_team_id,
        block_json
    from src,
        unnest(coalesce(json_query_array(src.payload, '$.response'), [])) as block_json
),

fixtures as (
    select
        league_code,
        raw_ingested_at,
        queried_team_id,
        fixture_el
    from team_blocks,
        unnest(
            coalesce(json_query_array(block_json, '$.response'), [])
        ) as fixture_el
)

select
    league_code,
    raw_ingested_at,
    queried_team_id,
    safe_cast(json_value(fixture_el, '$.fixture.id') as int64) as fixture_id,
    safe_cast(
        timestamp(json_value(fixture_el, '$.fixture.date'))
    as timestamp) as kickoff_datetime,
    safe_cast(
        date(timestamp(json_value(fixture_el, '$.fixture.date')))
    as date) as fixture_date,
    json_value(fixture_el, '$.fixture.status.short') as status_short,
    safe_cast(json_value(fixture_el, '$.league.id') as int64) as league_api_id,
    json_value(fixture_el, '$.league.name') as league_name,
    safe_cast(json_value(fixture_el, '$.league.season') as int64) as season,
    safe_cast(json_value(fixture_el, '$.teams.home.id') as int64) as home_team_id,
    json_value(fixture_el, '$.teams.home.name') as home_team_name,
    safe_cast(json_value(fixture_el, '$.teams.away.id') as int64) as away_team_id,
    json_value(fixture_el, '$.teams.away.name') as away_team_name,
    safe_cast(json_value(fixture_el, '$.goals.home') as int64) as goals_home,
    safe_cast(json_value(fixture_el, '$.goals.away') as int64) as goals_away,
    to_json_string(fixture_el) as source_json
from fixtures
where safe_cast(json_value(fixture_el, '$.fixture.id') as int64) is not null
qualify row_number() over (
    partition by queried_team_id, safe_cast(json_value(fixture_el, '$.fixture.id') as int64)
    order by raw_ingested_at desc
) = 1
