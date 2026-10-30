{#
  int_team_profile__yoy compares each team's current domestic league season through its N matches
  played with the same team's previous season in that league through its first N (fewer if that
  season had fewer), recomputed here from int_legs__team_match: the team's latest season in the
  league, its match count N, the previous season's cutoff, and the goals on each side, summed over
  exactly those matches (a forfeit counts in both, as in the league table). The points on each
  side are the rebuilt table's (int_team_season__table_by_time) at the kick-off of that side's
  last match. The previous side is empty when the team did not play the league the season before.

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
        l.kickoff_datetime,
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

expected_sums as (
    select
        c.team_sk,
        c.league_code,
        c.season_api_year,
        c.games_played as cutoff,
        max(if(d.season_api_year = c.season_api_year - 1, d.match_number, null)) as games_played_prev,
        max(if(d.season_api_year = c.season_api_year, d.kickoff_datetime, null)) as kickoff_this_season,
        max(if(d.season_api_year = c.season_api_year - 1, d.kickoff_datetime, null)) as kickoff_prev_season,
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

expected as (
    select
        s.*,
        cur_t.table_points as points_this_season,
        prev_t.table_points as points_prev_season
    from expected_sums as s
    left join {{ ref('int_team_season__table_by_time') }} as cur_t
        on
            s.team_sk = cur_t.team_sk
            and s.league_code = cur_t.league_code
            and s.season_api_year = cur_t.season_api_year
            and s.kickoff_this_season = cur_t.table_at
    left join {{ ref('int_team_season__table_by_time') }} as prev_t
        on
            s.team_sk = prev_t.team_sk
            and s.league_code = prev_t.league_code
            and s.season_api_year - 1 = prev_t.season_api_year
            and s.kickoff_prev_season = prev_t.table_at
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
    or e.points_this_season is distinct from m.points_this_season
    or e.points_prev_season is distinct from m.points_prev_season
    or e.goals_this_season != m.goals_this_season
    or e.goals_prev_season is distinct from m.goals_prev_season
    or e.goals_against_this_season != m.goals_against_this_season
    or e.goals_against_prev_season is distinct from m.goals_against_prev_season
