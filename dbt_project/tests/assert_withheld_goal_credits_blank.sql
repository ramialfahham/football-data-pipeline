{#
  A scorer or assister withheld on a goal that counts is credited no goal or assist in that match.
  Returns one row per player in fct_fixture_player_stats who carries goals as the withheld scorer
  of a goal other than an own goal, or assists as its withheld assister, on either player path:
  a provider stat line or a team sheet.
#}
{{ config(store_failures = true, severity = 'error') }}

with withheld as (
    select
        e.fixture_id,
        'scorer' as attribution,
        e.player_id
    from {{ ref('base_apif__fixture_events') }} as e
    inner join {{ ref('fct_fixture_event') }} as f
        on e.fixture_id = f.fixture_api_id and e.event_index = f.event_index
    where f.is_goal and f.scorer_needs_research and not f.is_own_goal and e.player_id is not null
    union all
    select
        e.fixture_id,
        'assister' as attribution,
        e.assist_player_id as player_id
    from {{ ref('base_apif__fixture_events') }} as e
    inner join {{ ref('fct_fixture_event') }} as f
        on e.fixture_id = f.fixture_api_id and e.event_index = f.event_index
    where f.is_goal and f.assist_needs_research and e.assist_player_id is not null
)

select
    w.fixture_id,
    w.attribution,
    w.player_id,
    s.goals,
    s.assists,
    s.is_from_lineups
from withheld as w
inner join {{ ref('fct_fixture_player_stats') }} as s
    on w.fixture_id = s.fixture_api_id and w.player_id = s.player_api_id
where
    (w.attribution = 'scorer' and s.goals > 0)
    or (w.attribution = 'assister' and s.assists > 0)
