{{ config(severity = 'error', store_failures = true) }}

-- A match decided after extra time counts its goals after minute 90. Fails a match whose score
-- equals its goal events of the first 90 minutes while goal events after minute 90 exist: that
-- score stopped at 90 minutes. Goal events are goals, penalties and own goals with a player,
-- shoot-out kicks left out, in matches where every goal event has a minute.

with goal_events as (
    select
        fixture_sk,
        team_sk,
        minute_elapsed
    from {{ ref('fct_fixture_event') }}
    where
        event_type = 'Goal'
        and event_detail in ('Normal Goal', 'Penalty', 'Own Goal')
        and event_comments is distinct from 'Penalty Shootout'
        and player_sk is not null
),

goal_counts as (
    select
        f.fixture_sk,
        f.league_code,
        f.goals_home,
        f.goals_away,
        countif(e.team_sk = f.home_team_sk and e.minute_elapsed <= 90) as home_goals_in_90,
        countif(e.team_sk = f.away_team_sk and e.minute_elapsed <= 90) as away_goals_in_90,
        countif(e.minute_elapsed > 90) as goals_after_90,
        countif(e.minute_elapsed is null) as goals_without_minute
    from {{ ref('fct_fixture') }} as f
    inner join goal_events as e
        on f.fixture_sk = e.fixture_sk
    where f.status_short in ('AET', 'PEN')
    group by f.fixture_sk, f.league_code, f.goals_home, f.goals_away
)

select *
from goal_counts
where
    goals_without_minute = 0
    and goals_after_90 > 0
    and home_goals_in_90 = goals_home
    and away_goals_in_90 = goals_away
