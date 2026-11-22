{#
  The rows of base_apif__fixtures_next, with the score of a match decided after extra time withheld
  where it stopped at 90 minutes: its goal events of the first 90 minutes add up to the score while
  an open-play goal or an own goal comes after minute 90 (score_stops_at_90). The match then
  carries result_needs_research, and its goals, shoot-out and winner are blank until research stands
  in fixture_result_corrections, as for every other withheld result. This is its own model because
  base_apif__fixture_events reads base_apif__fixtures_next. Every model downstream of the events
  that reads a score reads it here.

  Grain: fixture_id.
#}

with fixtures as (
    select * from {{ ref('base_apif__fixtures_next') }}
),

goal_counts as (
    select
        fixtures.fixture_id,
        countif(events.team_id = cast(fixtures.home_team_id as int64) and events.minute_elapsed <= 90)
            as home_goals_in_90,
        countif(events.team_id = cast(fixtures.away_team_id as int64) and events.minute_elapsed <= 90)
            as away_goals_in_90,
        countif(events.minute_elapsed > 90 and events.event_detail in ('Normal Goal', 'Own Goal'))
            as open_play_goals_after_90,
        countif(events.minute_elapsed is null) as goals_without_minute
    from fixtures
    inner join {{ ref('base_apif__fixture_events') }} as events
        on fixtures.fixture_id = events.fixture_id
    where
        fixtures.status_short in ('AET', 'PEN')
        and events.is_goal
        and coalesce(safe_cast(events.player_id as int64), 0) != 0
    group by fixtures.fixture_id
),

checked as (
    select
        fixtures.*,
        {{ score_stopped_at_90(
            'fixtures.goals_home', 'fixtures.goals_away', 'goal_counts.home_goals_in_90',
            'goal_counts.away_goals_in_90', 'goal_counts.open_play_goals_after_90',
            'goal_counts.goals_without_minute'
        ) }} as score_stops_at_90
    from fixtures
    left join goal_counts
        on fixtures.fixture_id = goal_counts.fixture_id
)

select
    * except (goals_home, goals_away, shootout_home, shootout_away, winner_team_id, result_needs_research),
    result_needs_research or score_stops_at_90 as result_needs_research,
    if(score_stops_at_90, null, goals_home) as goals_home,
    if(score_stops_at_90, null, goals_away) as goals_away,
    if(score_stops_at_90, null, shootout_home) as shootout_home,
    if(score_stops_at_90, null, shootout_away) as shootout_away,
    if(score_stops_at_90, null, winner_team_id) as winner_team_id
from checked
