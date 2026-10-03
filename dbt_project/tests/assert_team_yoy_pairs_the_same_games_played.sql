{#
  int_team_profile__yoy compares each team's current domestic league season through its N matches
  played with the same team's previous season in that league through its first N (fewer if that
  season had fewer), recomputed here from int_legs__team_match: the team's latest season in the
  league, its match count N, the previous season's cutoff, and the points and goals on each side,
  summed over exactly those matches (a forfeit counts in both, as in the league table). The
  previous side is empty when the team did not play the league the season before.

  One row per (team, league) whose pairing or totals differ, or that exists on one side only.
#}
{{ config(store_failures = true, severity = 'error') }}

with domestic_legs as (
    select
        l.team_sk,
        l.league_code,
        l.season_api_year,
        l.goals,
        l.goals_against,
        case l.result when 'W' then 3 when 'D' then 1 else 0 end as points,
        row_number() over (
            partition by l.team_sk, l.league_code, l.season_api_year
            order by l.kickoff_datetime asc, l.fixture_sk asc
        ) as match_number
    from {{ ref('int_legs__team_match') }} as l
    inner join {{ ref('competition_registry') }} as r
        on l.league_code = r.league_code
    where r.competition_type = 'domestic_league'
),

current_seasons as (
    select
        team_sk,
        league_code,
        season_api_year,
        max(match_number) as games_played
    from domestic_legs
    group by team_sk, league_code, season_api_year
    qualify row_number() over (partition by team_sk, league_code order by season_api_year desc) = 1
),

expected as (
    select
        c.team_sk,
        c.league_code,
        c.season_api_year,
        c.games_played as cutoff,
        max(if(d.season_api_year = c.season_api_year - 1, d.match_number, null)) as games_played_prev,
        sum(if(d.season_api_year = c.season_api_year, d.points, 0)) as points_this_season,
        sum(if(d.season_api_year = c.season_api_year - 1, d.points, null)) as points_prev_season,
        sum(if(d.season_api_year = c.season_api_year, d.goals, 0)) as goals_this_season,
        sum(if(d.season_api_year = c.season_api_year - 1, d.goals, null)) as goals_prev_season,
        sum(if(d.season_api_year = c.season_api_year, d.goals_against, 0)) as goals_against_this_season,
        sum(if(d.season_api_year = c.season_api_year - 1, d.goals_against, null)) as goals_against_prev_season
    from current_seasons as c
    inner join domestic_legs as d
        on
            c.team_sk = d.team_sk
            and c.league_code = d.league_code
            and d.season_api_year in (c.season_api_year, c.season_api_year - 1)
            and d.match_number <= c.games_played
    group by c.team_sk, c.league_code, c.season_api_year, c.games_played
),

model as (
    select
        team_sk,
        league_code,
        season_api_year,
        yoy_games_played_cutoff as cutoff,
        games_played_prev,
        points_this_season,
        points_prev_season,
        goals_for_this_season as goals_this_season,
        goals_for_prev_season as goals_prev_season,
        goals_against_this_season,
        goals_against_prev_season
    from {{ ref('int_team_profile__yoy') }}
)

select
    coalesce(e.team_sk, m.team_sk) as team_sk,
    coalesce(e.league_code, m.league_code) as league_code,
    to_json_string(e) as expected,
    to_json_string(m) as model
from expected as e
full outer join model as m
    on e.team_sk = m.team_sk and e.league_code = m.league_code
where
    e.team_sk is null
    or m.team_sk is null
    or e.season_api_year != m.season_api_year
    or e.cutoff != m.cutoff
    or e.games_played_prev is distinct from m.games_played_prev
    or e.points_this_season != m.points_this_season
    or e.points_prev_season is distinct from m.points_prev_season
    or e.goals_this_season != m.goals_this_season
    or e.goals_prev_season is distinct from m.goals_prev_season
    or e.goals_against_this_season != m.goals_against_this_season
    or e.goals_against_prev_season is distinct from m.goals_against_prev_season
