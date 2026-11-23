{#
  A match decided after extra time whose score stopped at 90 minutes has its result withheld: the
  match has result_needs_research and no score, shoot-out or winner in fct_fixture, and is on
  mart_competition_research_list as result_withheld, until a row in fixture_result_corrections with
  its sources settles it. Such a match has goal events of the first 90 minutes that add up to its
  score, every goal with a minute, and an open-play goal or an own goal after minute 90. A penalty
  after minute 90 is no evidence, because the provider files some shoot-outs as penalty goals
  without the shoot-out label. The stopped scores are derived here from the provider's score and the
  goal events, in SQL of their own and not through the macro and the flag. Returns a stopped score
  that fct_fixture still shows or that is not on the list, and a score that base withholds although
  it did not stop.
#}
{{ config(store_failures = true, severity = 'error') }}

with goal_counts as (
    select
        f.fixture_id,
        f.goals_home,
        f.goals_away,
        countif(e.team_id = cast(f.home_team_id as int64) and e.minute_elapsed <= 90) as home_goals_in_90,
        countif(e.team_id = cast(f.away_team_id as int64) and e.minute_elapsed <= 90) as away_goals_in_90,
        countif(e.minute_elapsed > 90 and e.event_detail in ('Normal Goal', 'Own Goal')) as open_play_goals_after_90,
        countif(e.minute_elapsed is null) as goals_without_minute
    from {{ ref('base_apif__fixtures_next') }} as f
    inner join {{ ref('base_apif__fixture_events') }} as e
        on f.fixture_id = e.fixture_id
    where
        f.status_short in ('AET', 'PEN')
        and e.is_goal
        and coalesce(safe_cast(e.player_id as int64), 0) != 0
    group by f.fixture_id, f.goals_home, f.goals_away
),

stopped as (
    select fixture_id
    from goal_counts
    where
        goals_without_minute = 0
        and open_play_goals_after_90 > 0
        and home_goals_in_90 = goals_home
        and away_goals_in_90 = goals_away
),

listed as (
    select fixture_sk
    from {{ ref('mart_competition_research_list') }}
    where check_name = 'result_withheld'
)

select
    s.fixture_id,
    'stopped score is shown' as failure
from stopped as s
inner join {{ ref('fct_fixture') }} as f
    on s.fixture_id = f.fixture_api_id
where
    not f.result_needs_research
    or f.goals_home is not null
    or f.goals_away is not null
    or f.shootout_home is not null
    or f.shootout_away is not null
    or f.winner_team_sk is not null

union all

select
    s.fixture_id,
    'stopped score is not on the list' as failure
from stopped as s
left join listed as l
    on cast(s.fixture_id as int64) = l.fixture_sk
where l.fixture_sk is null

union all

select
    c.fixture_id,
    'score is withheld though it did not stop' as failure
from {{ ref('base_apif__fixtures_checked') }} as c
left join stopped as s
    on c.fixture_id = s.fixture_id
where c.score_stops_at_90 and s.fixture_id is null
