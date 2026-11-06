{#
  A team's rows in base_apif__fixture_players_from_lineups hold every goal of its score, where the
  provider sent no stat line for the team: its players' goals plus the own goals filed under it.
  Returns one row per team match that misses the
  score, a match with no goal events included: a blank goals value is a miss. The fix is sourced
  goals in fixture_goal_corrections.
#}
{{ config(store_failures = true, severity = 'error') }}

with fixtures as (
    select
        fixture_id,
        goals_home,
        goals_away,
        cast(home_team_id as int64) as home_team_id
    from {{ ref('base_apif__fixtures_next') }}
),

own_goals as (
    select
        fixture_id,
        team_id,
        count(*) as own_goals
    from {{ ref('base_apif__fixture_events') }}
    where is_goal and is_own_goal
    group by fixture_id, team_id
),

provider_teams as (
    select distinct
        fixture_id,
        team_id
    from {{ ref('base_apif__fixture_players') }}
),

teams as (
    select
        l.league_code,
        l.fixture_id,
        l.team_id,
        countif(l.goals is null) as players_with_blank_goals,
        coalesce(sum(l.goals), 0) as player_goals
    from {{ ref('base_apif__fixture_players_from_lineups') }} as l
    left join provider_teams as p
        on l.fixture_id = p.fixture_id and l.team_id = p.team_id
    where p.fixture_id is null
    group by l.league_code, l.fixture_id, l.team_id
)

select
    t.league_code,
    t.fixture_id,
    t.team_id,
    t.players_with_blank_goals,
    t.player_goals,
    coalesce(o.own_goals, 0) as own_goals,
    if(t.team_id = f.home_team_id, f.goals_home, f.goals_away) as score
from teams as t
inner join fixtures as f
    on t.fixture_id = f.fixture_id
left join own_goals as o
    on t.fixture_id = o.fixture_id and t.team_id = o.team_id
where
    t.players_with_blank_goals > 0
    or t.player_goals + coalesce(o.own_goals, 0) != if(t.team_id = f.home_team_id, f.goals_home, f.goals_away)
