-- Each fixture's score; after extra time it comes from the goal events where the provider's
-- score stops at 90 minutes.
with import_base_apif__fixtures_next as (
    select * from {{ ref('base_apif__fixtures_next') }}
),

import_base_apif__fixture_events as (
    select * from {{ ref('base_apif__fixture_events') }}
),

goal_events as (
    select
        fixture_id,
        team_id,
        minute_elapsed
    from import_base_apif__fixture_events
    where
        event_type = 'Goal'
        and event_detail in ('Normal Goal', 'Penalty', 'Own Goal')
        and event_comments is distinct from 'Penalty Shootout'
        and player_id is not null
),

goal_counts as (
    select
        fixtures.fixture_id,
        countif(
            goal_events.team_id = cast(fixtures.home_team_id as int64)
            and goal_events.minute_elapsed <= 90
        ) as home_goals_in_90,
        countif(
            goal_events.team_id = cast(fixtures.away_team_id as int64)
            and goal_events.minute_elapsed <= 90
        ) as away_goals_in_90,
        countif(
            goal_events.team_id = cast(fixtures.home_team_id as int64)
            and goal_events.minute_elapsed > 90
        ) as home_goals_after_90,
        countif(
            goal_events.team_id = cast(fixtures.away_team_id as int64)
            and goal_events.minute_elapsed > 90
        ) as away_goals_after_90,
        countif(goal_events.minute_elapsed is null) as goals_without_minute
    from import_base_apif__fixtures_next as fixtures
    inner join goal_events
        on fixtures.fixture_id = goal_events.fixture_id
    group by fixtures.fixture_id
),

scores as (
    select
        fixtures.fixture_id,
        fixtures.goals_home,
        fixtures.goals_away,
        goal_counts.home_goals_after_90,
        goal_counts.away_goals_after_90,
        coalesce(
            fixtures.status_short in ('AET', 'PEN')
            and fixtures.result_correction_source is null
            and goal_counts.goals_without_minute = 0
            and goal_counts.home_goals_in_90 = fixtures.goals_home
            and goal_counts.away_goals_in_90 = fixtures.goals_away
            and goal_counts.home_goals_after_90 + goal_counts.away_goals_after_90 > 0,
            false
        ) as is_score_from_goal_events
    from import_base_apif__fixtures_next as fixtures
    left join goal_counts
        on fixtures.fixture_id = goal_counts.fixture_id
)

select
    fixture_id,
    is_score_from_goal_events,
    if(is_score_from_goal_events, goals_home + home_goals_after_90, goals_home) as goals_home,
    if(is_score_from_goal_events, goals_away + away_goals_after_90, goals_away) as goals_away
from scores
