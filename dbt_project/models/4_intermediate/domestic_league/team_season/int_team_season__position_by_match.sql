{#
  A domestic league's table at every number of matches played: each team's position after its
  Nth match of the season, ranked by points, then goal difference, then goals scored, within its
  section of that season's official table (an MLS conference). rank(), so teams level on all three
  share a place. The year-over-year comparison reads last season's position at this season's N.

  Only a season where every team sits in one section that is a league, conference or group table:
  a season split into rounds, or with a team in two sections (an Apertura and a Clausura), has no
  position at a number of matches. Points come from the results, so a deduction the official table
  carries is not in them; assert_team_position_by_match_matches_final_table lists where the rank
  and the official table differ.

  Grain: (team_sk, league_code, season_api_year, match_number).
#}

with cml as (
    select
        team_sk,
        league_code,
        season_api_year,
        match_number,
        points_won,
        goals,
        goals_against
    from {{ ref('int_team_season__metrics_cumulative') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

sections as (
    select
        s.league_code,
        s.season_api_year,
        s.team_sk,
        s.group_name,
        k.table_kind
    from {{ ref('fct_standings') }} as s
    inner join {{ ref('int_standings__section_kinds') }} as k
        on s.group_name = k.group_name
    where k.table_kind != 'ranking'
),

-- seasons whose every team is in one league, conference or group table
single_table_seasons as (
    select
        league_code,
        season_api_year
    from sections
    group by league_code, season_api_year
    having
        countif(table_kind = 'split_round') = 0
        and count(*) = count(distinct team_sk)
),

team_sections as (
    select s.*
    from sections as s
    inner join single_table_seasons as t
        on
            s.league_code = t.league_code
            and s.season_api_year = t.season_api_year
)

select
    c.team_sk,
    c.league_code,
    c.season_api_year,
    c.match_number,
    ts.group_name,
    c.points_won,
    c.goals as goals_for,
    c.goals - c.goals_against as goal_difference,
    rank() over (
        partition by c.league_code, c.season_api_year, ts.group_name, c.match_number
        order by c.points_won desc, c.goals - c.goals_against desc, c.goals desc
    ) as position_at_match
from cml as c
inner join registry as r
    on c.league_code = r.league_code
inner join team_sections as ts
    on
        c.team_sk = ts.team_sk
        and c.league_code = ts.league_code
        and c.season_api_year = ts.season_api_year
where r.competition_type = 'domestic_league'
