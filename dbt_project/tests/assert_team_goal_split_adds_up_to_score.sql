{{ config(severity = 'error', store_failures = true) }}

-- A team's goals are its open-play goals, its penalties and the own goals credited to it, nothing
-- else. Open-play goals are counted from the events here, so the model's goals_penalty and goals_own
-- are checked against the scoreline rather than against their own difference. The provider files an
-- own goal under the team it counts for, and a shoot-out kick is no goal. Only team-matches whose
-- goal events add up to the team's score are checked: elsewhere the events are incomplete or credit
-- the wrong team, and the split is blank unless the team scored none. Anywhere the split is known it
-- is at most the score.

with goal_events as (
    select
        fixture_sk,
        team_sk,
        event_detail
    from {{ ref('fct_fixture_event') }}
    where
        event_type = 'Goal'
        and event_detail in ('Normal Goal', 'Penalty', 'Own Goal')
        and event_comments is distinct from 'Penalty Shootout'
        and team_sk is not null
),

team_goal_events as (
    select
        fixture_sk,
        team_sk,
        count(*) as goal_events,
        countif(event_detail = 'Normal Goal') as goals_open_play_events
    from goal_events
    group by fixture_sk, team_sk
)

select
    l.fixture_sk,
    l.team_sk,
    l.league_code,
    l.goals,
    l.goals_penalty,
    l.goals_own,
    coalesce(e.goals_open_play_events, 0) as goals_open_play_events
from {{ ref('int_legs__team_match') }} as l
left join team_goal_events as e
    on l.fixture_sk = e.fixture_sk and l.team_sk = e.team_sk
where
    l.goals_penalty + l.goals_own > l.goals
    or (
        coalesce(e.goal_events, 0) = l.goals
        and l.goals_penalty is not null
        and l.goals_own is not null
        and coalesce(e.goals_open_play_events, 0) + l.goals_penalty + l.goals_own != l.goals
    )
