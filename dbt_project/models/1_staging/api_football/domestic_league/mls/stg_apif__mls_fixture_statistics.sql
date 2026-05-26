with src as (
    select *
    from {{ source('api_football', 'raw_apif_mls_fixture_details') }}
),

fixtures as (
    select
        src.ingested_at as raw_ingested_at,
        fixture_json,
        'MLS' as league_code
    from src,
        unnest(coalesce(json_query_array(src.payload, '$.response'), [])) as fixture_json
),

stats_rows as (
    select
        league_code,
        raw_ingested_at,
        stat_el,
        safe_cast(json_value(fixture_json, '$.fixture.id') as int64) as fixture_id
    from fixtures,
        unnest(json_query_array(fixture_json, '$.statistics')) as stat_el
),

stat_lines as (
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
),

pivoted as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_id,
        team_name,
        any_value(source_json) as source_json,
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
        end) as passes_accuracy_percent
    from stat_lines
    where
        fixture_id is not null
        and team_id is not null
    group by league_code, raw_ingested_at, fixture_id, team_id, team_name
)

select
    league_code,
    raw_ingested_at,
    fixture_id,
    team_id,
    team_name,
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
    source_json
from pivoted
