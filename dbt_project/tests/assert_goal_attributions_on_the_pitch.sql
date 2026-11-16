{#
  A goal names a scorer or assister only where the match's confirmed or researched line-up has him
  on the pitch at the goal's minute. Returns one row per provider goal in fct_fixture_event that
  names a player of the sheet who was not: such a player is withheld (scorer_needs_research,
  assist_needs_research). Minutes are elapsed * 100 + added time; a minute at the end of a period
  with no added minute can be any minute of that period's added time. A goal from
  fixture_goal_corrections is sourced and is not checked.
#}
{{ config(store_failures = true, severity = 'error') }}

with sheet as (
    select
        fixture_api_id,
        player_api_id,
        if(is_starter, 0, minute_on * 100 + coalesce(minute_on_extra, 0)) as on_from,
        if(
            minute_off is null,
            99999,
            minute_off * 100 + coalesce(minute_off_extra, if(minute_off in (45, 90, 105, 120), 99, 0))
        ) as off_to
    from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched')
),

goals as (
    select
        fixture_api_id,
        event_index,
        player_api_id,
        assist_player_api_id,
        minute_elapsed * 100 + coalesce(minute_extra, 0) as goal_from,
        minute_elapsed * 100 + coalesce(minute_extra, if(minute_elapsed in (45, 90, 105, 120), 99, 0)) as goal_to
    from {{ ref('fct_fixture_event') }}
    where is_goal and goal_correction_source is null and minute_elapsed is not null
),

named as (
    select
        fixture_api_id,
        event_index,
        'scorer' as attribution,
        player_api_id,
        goal_from,
        goal_to
    from goals
    where player_api_id is not null
    union all
    select
        fixture_api_id,
        event_index,
        'assister' as attribution,
        assist_player_api_id as player_api_id,
        goal_from,
        goal_to
    from goals
    where assist_player_api_id is not null
)

select
    n.fixture_api_id,
    n.event_index,
    n.attribution,
    n.player_api_id,
    n.goal_from,
    n.goal_to,
    s.on_from,
    s.off_to
from named as n
inner join sheet as s
    on n.fixture_api_id = s.fixture_api_id and n.player_api_id = s.player_api_id
where s.on_from is null or s.on_from > n.goal_to or s.off_to < n.goal_from
