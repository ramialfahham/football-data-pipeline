with source as (
    select *
    from {{ source('football_data', 'raw_sp1_2122') }}
)

select
    'SP1' as league,
    '2122' as season,
    'RAW_SP1_2122' as raw_table,
    Date as match_date,
    HomeTeam as home_team,
    AwayTeam as away_team,
    cast(FTHG as int64) as full_time_home_goals,
    cast(FTAG as int64) as full_time_away_goals,
    cast(FTR as string) as full_time_result
from source
