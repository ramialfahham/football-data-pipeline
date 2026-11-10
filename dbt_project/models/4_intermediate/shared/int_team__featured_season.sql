{#
  The season a team's page opens on: its most recent domestic league season, or, for a team with
  no league season, its most recent season of any type. Two seasons of one year go to the one with
  the latest match, then by league_code, as the Player page picks its featured season
  (int_player__page_profile). mart_team_profile flags it and the page's season window is anchored
  at it, so both read this one rule.

  Grain: (team_sk).
#}

with seasons as (
    select
        team_sk,
        season_sk,
        league_code,
        season_api_year
    from {{ ref('int_team_season__metrics') }}
),

latest_matches as (
    select
        team_sk,
        season_sk,
        max(kickoff_datetime) as latest_match_at
    from {{ ref('int_legs__team_match') }}
    group by team_sk, season_sk
),

competitions as (
    select
        league_code,
        competition_type
    from {{ ref('dim_league') }}
)

select
    s.team_sk,
    s.season_sk as featured_season_sk,
    s.league_code as featured_league_code,
    s.season_api_year as featured_season_api_year
from seasons as s
left join competitions as c
    on s.league_code = c.league_code
left join latest_matches as m
    on s.team_sk = m.team_sk and s.season_sk = m.season_sk
qualify row_number() over (
    partition by s.team_sk
    order by
        case when c.competition_type = 'domestic_league' then 0 else 1 end asc,
        s.season_api_year desc,
        m.latest_match_at desc,
        s.league_code asc
) = 1
