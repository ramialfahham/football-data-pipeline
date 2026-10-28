{#
  Each team's biggest win and heaviest defeat in a season, across every competition it played
  that season: the finished match with the widest margin. The competition page's rule for its
  biggest margin decides a tie: the match with more goals, then the earlier kickoff, then the
  fixture id. A season without a win (or without a defeat) has NULL in that half.
  Grain: (team_sk, season_api_year).
#}

with legs as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        team_sk,
        opponent_team_sk,
        home_away,
        kickoff_datetime,
        goals,
        goals_against,
        result
    from {{ ref('int_legs__team_match') }}
),

teams as (
    select distinct
        team_sk,
        season_api_year
    from legs
),

biggest_win as (
    select *
    from legs
    where result = 'W'
    qualify row_number() over (
        partition by team_sk, season_api_year
        order by
            goals - goals_against desc,
            goals + goals_against desc,
            kickoff_datetime asc,
            fixture_sk asc
    ) = 1
),

heaviest_defeat as (
    select *
    from legs
    where result = 'L'
    qualify row_number() over (
        partition by team_sk, season_api_year
        order by
            goals_against - goals desc,
            goals + goals_against desc,
            kickoff_datetime asc,
            fixture_sk asc
    ) = 1
)

select
    t.team_sk,
    t.season_api_year,
    w.fixture_sk as biggest_win_fixture_sk,
    w.league_code as biggest_win_league_code,
    w.opponent_team_sk as biggest_win_opponent_team_sk,
    w.home_away as biggest_win_home_away,
    w.goals as biggest_win_goals_for,
    w.goals_against as biggest_win_goals_against,
    w.kickoff_datetime as biggest_win_kickoff_datetime,
    d.fixture_sk as heaviest_defeat_fixture_sk,
    d.league_code as heaviest_defeat_league_code,
    d.opponent_team_sk as heaviest_defeat_opponent_team_sk,
    d.home_away as heaviest_defeat_home_away,
    d.goals as heaviest_defeat_goals_for,
    d.goals_against as heaviest_defeat_goals_against,
    d.kickoff_datetime as heaviest_defeat_kickoff_datetime
from teams as t
left join biggest_win as w
    on
        t.team_sk = w.team_sk
        and t.season_api_year = w.season_api_year
left join heaviest_defeat as d
    on
        t.team_sk = d.team_sk
        and t.season_api_year = d.season_api_year
