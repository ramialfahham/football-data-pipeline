-- Pivot the long-format staging rows (one per statistic line) into one wide row
-- per (fixture, team), then keep the latest ingest snapshot per (fixture, team).
-- The pivot is business reshaping and lives here in base, not in staging.
with stat_lines as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_id,
        stat_type,
        stat_value_raw
    from {{ ref('stg_apif__fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

pivoted as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_id,
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
    group by league_code, raw_ingested_at, fixture_id, team_id
),

deduped_fixture_statistics as (
    select *
    from pivoted
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    fixture_id,
    team_id,
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
    raw_ingested_at
from deduped_fixture_statistics
