with source as (
    select *
    from {{ source('football_data', 'raw_e0_1718') }}
)

select
    'E0' as league,
    '1718' as season,
    'RAW_E0_1718' as raw_table,
    Date as match_date,
    HomeTeam as home_team,
    AwayTeam as away_team,
    cast(FTHG as int64) as full_time_home_goals,
    cast(FTAG as int64) as full_time_away_goals,
    cast(FTR as string) as full_time_result
from source
