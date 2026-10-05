{#
  A team-season's goals, less the goals of its awarded matches (which no player scored), equal its
  players' goals at the club plus the own goals it was credited. Compared where both sides are
  known: every club-season row of the team has its players' goals, and the team's own goals are
  known. A team-season holding a match whose players' goals plus own goals miss the score is left
  out: assert_base_player_stats_cleaned (goals_do_not_add_up) fails any such match where either the
  per-player count or the goal events add up, so every match left out is one where neither does,
  the known exception of the results rule.

  Returns one row per disagreeing team-season, with both sides.
#}
{{ config(store_failures = true, severity = 'error') }}

with players_by_match as (
    select
        fixture_sk,
        team_sk,
        if(logical_and(goals is not null), sum(goals), null) as players_goals
    from {{ ref('int_legs__player_match') }}
    group by fixture_sk, team_sk
),

team_seasons as (
    select
        t.team_sk,
        t.season_sk,
        sum(if(t.is_awarded_result, t.goals, 0)) as awarded_goals,
        countif(
            not t.is_awarded_result
            and p.players_goals + t.goals_own != t.goals
        ) as matches_not_adding_up
    from {{ ref('int_legs__team_match') }} as t
    left join players_by_match as p
        on t.fixture_sk = p.fixture_sk and t.team_sk = p.team_sk
    group by t.team_sk, t.season_sk
),

club_seasons as (
    select
        team_sk,
        season_sk,
        if(logical_and(goals_player is not null), sum(goals_player), null) as players_goals
    from {{ ref('int_player_club_season__metrics') }}
    group by team_sk, season_sk
)

select
    m.league_code,
    m.season_api_year,
    m.team_sk,
    m.goals,
    ts.awarded_goals,
    c.players_goals,
    m.goals_own,
    (m.goals - ts.awarded_goals) - (c.players_goals + m.goals_own) as goals_difference
from {{ ref('int_team_season__metrics') }} as m
inner join team_seasons as ts
    on m.team_sk = ts.team_sk and m.season_sk = ts.season_sk
inner join club_seasons as c
    on m.team_sk = c.team_sk and m.season_sk = c.season_sk
where
    c.players_goals is not null
    and m.goals_own is not null
    and ts.matches_not_adding_up = 0
    and m.goals - ts.awarded_goals != c.players_goals + m.goals_own
