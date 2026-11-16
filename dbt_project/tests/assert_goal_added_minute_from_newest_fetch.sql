{#
  A goal keeps the newest added minute any fetch carried. Returns one row per scorer, detail and
  minute of a match where fct_fixture_event holds provider goals with no added minute while one
  fetch gave every such goal an added minute.
#}
{{ config(store_failures = true, severity = 'error') }}

with fetched as (
    select
        fixture_id,
        raw_ingested_at,
        player_id,
        event_detail,
        minute_elapsed,
        countif(minute_extra is not null) as goals_with_added_minute
    from {{ ref('stg_apif__fixture_events') }}
    where event_type = 'Goal' and player_id is not null and minute_elapsed is not null
    group by fixture_id, raw_ingested_at, player_id, event_detail, minute_elapsed
),

served as (
    select
        fixture_api_id as fixture_id,
        player_api_id as player_id,
        event_detail,
        minute_elapsed,
        count(*) as goals,
        countif(minute_extra is null) as goals_without_added_minute
    from {{ ref('fct_fixture_event') }}
    where event_type = 'Goal' and goal_correction_source is null and player_api_id is not null
    group by fixture_api_id, player_api_id, event_detail, minute_elapsed
)

select
    s.fixture_id,
    s.player_id,
    s.event_detail,
    s.minute_elapsed,
    s.goals,
    s.goals_without_added_minute,
    max(f.goals_with_added_minute) as most_goals_with_added_minute_in_one_fetch
from served as s
inner join fetched as f
    on
        s.fixture_id = f.fixture_id
        and s.player_id = f.player_id
        and s.event_detail = f.event_detail
        and s.minute_elapsed = f.minute_elapsed
where s.goals_without_added_minute > 0
group by s.fixture_id, s.player_id, s.event_detail, s.minute_elapsed, s.goals, s.goals_without_added_minute
having max(f.goals_with_added_minute) >= s.goals
