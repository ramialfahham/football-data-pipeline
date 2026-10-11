{{ config(severity = 'error', store_failures = true) }}

-- A match decided after extra time counts its goals after minute 90. Fails a match whose score
-- equals its goal events of the first 90 minutes while an open-play goal or an own goal after
-- minute 90 exists: that score stopped at 90 minutes. A penalty after minute 90 is no evidence,
-- because the provider files some shoot-outs as penalty goals without the shoot-out label. The fix
-- is a row in fixture_result_corrections with its sources.

with goal_events as (
    select
        fixture_sk,
        team_sk,
        minute_elapsed,
        event_detail
    from {{ ref('fct_fixture_event') }}
    where
        is_goal
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
        countif(e.minute_elapsed > 90 and e.event_detail in ('Normal Goal', 'Own Goal')) as open_play_goals_after_90,
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
    and open_play_goals_after_90 > 0
    and home_goals_in_90 = goals_home
    and away_goals_in_90 = goals_away
