with source as (
    select *
    from {{ source('football_data', 'raw_f1_2021') }}
)

select
    'F1' as league,
    '2021' as season,
    'RAW_F1_2021' as raw_table,
    Date as match_date,
    HomeTeam as home_team,
    AwayTeam as away_team,
    cast(FTHG as int64) as full_time_home_goals,
    cast(FTAG as int64) as full_time_away_goals,
    cast(FTR as string) as full_time_result
from source
