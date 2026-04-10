with source as (
    select *
    from {{ source('football_data', 'raw_i1_1112') }}
)

select
    'I1' as league,
    '1112' as season,
    'RAW_I1_1112' as raw_table,
    Date as match_date,
    HomeTeam as home_team,
    AwayTeam as away_team,
    cast(FTHG as int64) as full_time_home_goals,
    cast(FTAG as int64) as full_time_away_goals,
    cast(FTR as string) as full_time_result
from source
