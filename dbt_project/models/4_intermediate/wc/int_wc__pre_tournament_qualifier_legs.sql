{{ config(materialized='table') }}

{#
  Finished qualifier legs used for WC pre-tournament metrics.
  Grain: (team_sk, fixture_sk). Includes supporting confederation leagues until the team's
  first finished WC tournament leg in the target season (none yet for WC 2026 participants).
#}

with import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

import_int_wc__participant_teams as (
    select * from {{ ref('int_wc__participant_teams') }}
),

supporting_leagues as (
    select
        supporting_league_code as league_code,
        qualifier_season_api_year
    from {{ ref('wc_supporting_league_codes') }}
),

first_wc_tournament_leg as (
    select
        leg.team_sk,
        min(leg.kickoff_datetime) as first_wc_kickoff_datetime
    from import_int_matchday__finished_fixture_team_leg as leg
    inner join import_int_wc__participant_teams as pt
        on
            leg.team_sk = pt.team_sk
            and leg.league_code = pt.league_code
            and leg.season_api_year = pt.season_api_year
    group by leg.team_sk
),

qualifier_legs_raw as (
    select
        leg.fixture_sk,
        leg.team_sk,
        leg.league_sk,
        leg.season_sk,
        leg.league_code,
        leg.season_api_year,
        leg.kickoff_datetime,
        leg.round_name,
        leg.round_order,
        leg.goals_for,
        leg.goals_against,
        leg.result,
        leg.shots_on_goal,
        leg.shots_total,
        leg.shots_inside_box,
        leg.corner_kicks,
        leg.passes_total,
        leg.passes_accurate,
        leg.goalkeeper_saves,
        leg.opponent_total_shots,
        leg.opponent_corner_kicks,
        pt.league_code as tournament_league_code,
        pt.season_api_year as tournament_season_api_year
    from import_int_matchday__finished_fixture_team_leg as leg
    inner join import_int_wc__participant_teams as pt
        on leg.team_sk = pt.team_sk
    inner join supporting_leagues as sl
        on
            leg.league_code = sl.league_code
            and leg.season_api_year = sl.qualifier_season_api_year
    left join first_wc_tournament_leg as fw
        on leg.team_sk = fw.team_sk
    where
        fw.first_wc_kickoff_datetime is null
        or leg.kickoff_datetime < fw.first_wc_kickoff_datetime
),

qualifier_legs_dedup as (
    select * except (leg_dedup_rn)
    from (
        select
            *,
            row_number() over (
                partition by team_sk, fixture_sk
                order by kickoff_datetime desc, fixture_sk desc
            ) as leg_dedup_rn
        from qualifier_legs_raw
    )
    where leg_dedup_rn = 1
)

select *
from qualifier_legs_dedup
