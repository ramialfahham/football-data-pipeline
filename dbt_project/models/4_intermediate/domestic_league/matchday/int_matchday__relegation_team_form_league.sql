{{ config(materialized='table') }}

{#
  Per (upcoming fixture_sk, team_sk): which domestic league supplies form (BL1 vs BL2).
  Rule: among BL1/BL2 finished legs in the fixture season, pick the league with the most legs;
  tie-break prefers BL1. Wolfsburg → BL1; 3rd-place BL2 side → BL2.
  Grain: (fixture_sk, team_sk).
#}

with relegation_fixtures as (
    select * from {{ ref('int_matchday__relegation_upcoming_fixtures') }}
),

finished_legs as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

team_fixture as (
    select
        rf.fixture_sk,
        rf.season_api_year,
        rf.home_team_sk as team_sk
    from relegation_fixtures as rf
    union all
    select
        rf.fixture_sk,
        rf.season_api_year,
        rf.away_team_sk as team_sk
    from relegation_fixtures as rf
),

leg_counts as (
    select
        tf.fixture_sk,
        tf.team_sk,
        tf.season_api_year,
        fl.league_code,
        count(*) as finished_legs_in_league
    from team_fixture as tf
    inner join finished_legs as fl
        on
            tf.team_sk = fl.team_sk
            and tf.season_api_year = fl.season_api_year
            and fl.league_code in ('BL1', 'BL2')
    group by tf.fixture_sk, tf.team_sk, tf.season_api_year, fl.league_code
),

ranked as (
    select
        *,
        row_number() over (
            partition by fixture_sk, team_sk
            order by
                finished_legs_in_league desc,
                case league_code when 'BL1' then 0 when 'BL2' then 1 else 2 end
        ) as league_pick_rn
    from leg_counts
)

select
    fixture_sk,
    team_sk,
    season_api_year,
    league_code as form_league_code,
    finished_legs_in_league
from ranked
where league_pick_rn = 1
