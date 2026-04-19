{{ config(materialized='table') }}

{#
    API-Football exposes fixture stats as an array of {type, value} pairs.
    Pivot to named columns; percent-valued metrics (possession, pass accuracy)
    are delivered as strings like "52%" and are stripped + cast to INT64.
#}

with src as (
    select
        league_code,
        fixture_id,
        team_id,
        statistics_lines_json,
        raw_ingested_at,
        row_number() over (
            partition by fixture_id, team_id
            order by raw_ingested_at desc
        ) as rn
    from {{ ref('stg_apif__d1_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

latest as (
    select * from src
    where rn = 1
),

stat_lines as (
    select
        league_code,
        fixture_id,
        team_id,
        raw_ingested_at,
        json_value(stat_el, '$.type') as stat_type,
        json_value(stat_el, '$.value') as stat_value_raw
    from latest,
        unnest(json_query_array(statistics_lines_json, '$')) as stat_el
),

pivoted as (
    select
        league_code,
        fixture_id,
        team_id,
        raw_ingested_at,
        max(case when stat_type = 'Shots on Goal' then safe_cast(stat_value_raw as int64) end)
            as shots_on_goal,
        max(case when stat_type = 'Shots off Goal' then safe_cast(stat_value_raw as int64) end)
            as shots_off_goal,
        max(case when stat_type = 'Total Shots' then safe_cast(stat_value_raw as int64) end)
            as shots_total,
        max(case when stat_type = 'Blocked Shots' then safe_cast(stat_value_raw as int64) end)
            as shots_blocked,
        max(case when stat_type = 'Shots insidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_inside_box,
        max(case when stat_type = 'Shots outsidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_outside_box,
        max(case when stat_type = 'Fouls' then safe_cast(stat_value_raw as int64) end)
            as fouls,
        max(case when stat_type = 'Corner Kicks' then safe_cast(stat_value_raw as int64) end)
            as corner_kicks,
        max(case when stat_type = 'Offsides' then safe_cast(stat_value_raw as int64) end)
            as offsides,
        max(case
            when stat_type = 'Ball Possession'
                then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)
        end) as ball_possession_percent,
        max(case when stat_type = 'Yellow Cards' then safe_cast(stat_value_raw as int64) end)
            as yellow_cards,
        max(case when stat_type = 'Red Cards' then safe_cast(stat_value_raw as int64) end)
            as red_cards,
        max(case when stat_type = 'Goalkeeper Saves' then safe_cast(stat_value_raw as int64) end)
            as goalkeeper_saves,
        max(case when stat_type = 'Total passes' then safe_cast(stat_value_raw as int64) end)
            as passes_total,
        max(case when stat_type = 'Passes accurate' then safe_cast(stat_value_raw as int64) end)
            as passes_accurate,
        max(case
            when stat_type = 'Passes %'
                then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)
        end) as passes_accuracy_percent,
        max(case when stat_type = 'expected_goals' then safe_cast(stat_value_raw as float64) end)
            as expected_goals
    from stat_lines
    group by league_code, fixture_id, team_id, raw_ingested_at
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'league_code', 'team_id']) }}
        as fixture_team_stat_sk,
    cast(fixture_id as int64) as fixture_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'team_id']) }} as team_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    shots_on_goal,
    shots_off_goal,
    shots_total,
    shots_blocked,
    shots_inside_box,
    shots_outside_box,
    fouls,
    corner_kicks,
    offsides,
    ball_possession_percent,
    yellow_cards,
    red_cards,
    goalkeeper_saves,
    passes_total,
    passes_accurate,
    passes_accuracy_percent,
    expected_goals,
    raw_ingested_at
from pivoted
