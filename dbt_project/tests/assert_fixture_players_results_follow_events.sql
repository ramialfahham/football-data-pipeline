{#
  Where another fetch gives a player the goals, assists or cards of the match's events and the
  match's picked fetch does not, the events' count is his. Where the picked fetch leaves his minutes
  blank, another fetch's minutes are his when a substitution brought him on that many minutes before
  the 90th, the minute of entry counted or not. Returns one row per player-match and result where
  base_apif__fixture_players shows something else, unless the cleaning changed that result (a
  stat_corrections entry).
#}
{{ config(store_failures = true, severity = 'error') }}

with fetch_rows as (
    select
        stat_line.league_code,
        stat_line.fixture_id,
        stat_line.raw_ingested_at,
        stat_line.goals_total,
        stat_line.goals_assists,
        stat_line.cards_yellow,
        stat_line.cards_red,
        stat_line.minutes_played,
        {{ fixture_player_id(
            'stat_line.player_id', 'stat_line.fixture_id', 'stat_line.team_id', 'stat_line.shirt_number'
        ) }} as player_id,
        logical_or(stat_line.goals_against is not null)
            over (partition by stat_line.league_code, stat_line.fixture_id, stat_line.raw_ingested_at)
            as fetch_is_complete
    from {{ ref('stg_apif__fixture_players') }} as stat_line
    where stat_line.fixture_id is not null and stat_line.team_id is not null
),

per_fetch as (
    select
        league_code,
        fixture_id,
        player_id,
        raw_ingested_at,
        goals_total,
        goals_assists,
        cards_yellow,
        cards_red,
        minutes_played,
        raw_ingested_at = coalesce(
            max(if(fetch_is_complete, raw_ingested_at, null)) over (partition by league_code, fixture_id),
            max(raw_ingested_at) over (partition by league_code, fixture_id)
        ) as is_picked
    from fetch_rows
    where player_id is not null and player_id != 0
),

matches_with_events as (
    select fixture_id
    from {{ ref('base_apif__fixture_events') }}
    group by fixture_id
    having logical_or(has_full_events)
),

event_counts as (
    select
        e.fixture_id,
        counted.player_id,
        countif(counted.result_name = 'goals') as goals,
        countif(counted.result_name = 'assists') as assists,
        countif(counted.result_name = 'cards_yellow') as cards_yellow,
        countif(counted.result_name = 'cards_red') as cards_red
    from {{ ref('base_apif__fixture_events') }} as e
    inner join matches_with_events as m
        on e.fixture_id = m.fixture_id
    cross join
        unnest([
            struct(
                'goals' as result_name,
                if(e.is_goal and not e.is_own_goal, e.player_id, null) as player_id
            ),
            struct('assists', if(e.is_goal and not e.is_own_goal, e.assist_player_id, null)),
            struct(
                'cards_yellow',
                if(
                    e.event_type = 'Card' and e.event_detail = 'Yellow Card'
                    and coalesce(e.event_comments, '') != 'Not on pitch' and e.has_full_events,
                    e.player_id,
                    null
                )
            ),
            struct(
                'cards_red',
                if(
                    e.event_type = 'Card' and e.event_detail = 'Red Card'
                    and coalesce(e.event_comments, '') != 'Not on pitch' and e.has_full_events,
                    e.player_id,
                    null
                )
            )
        ]) as counted
    where counted.player_id is not null
    group by e.fixture_id, counted.player_id
),

fetch_results as (
    select
        f.league_code,
        f.fixture_id,
        f.player_id,
        f.is_picked,
        fetched.result_name,
        coalesce(fetched.result_value, 0) as result_value,
        coalesce(
            case fetched.result_name
                when 'goals' then c.goals
                when 'assists' then c.assists
                when 'cards_yellow' then c.cards_yellow
                when 'cards_red' then c.cards_red
            end,
            0
        ) as event_value
    from per_fetch as f
    inner join matches_with_events as m
        on f.fixture_id = m.fixture_id
    left join event_counts as c
        on f.fixture_id = c.fixture_id and f.player_id = c.player_id
    cross join
        unnest([
            struct('goals' as result_name, f.goals_total as result_value),
            struct('assists', f.goals_assists),
            struct('cards_yellow', f.cards_yellow),
            struct('cards_red', f.cards_red)
        ]) as fetched
),

settled as (
    select
        league_code,
        fixture_id,
        player_id,
        result_name,
        min(event_value) as events_count
    from fetch_results
    group by league_code, fixture_id, player_id, result_name
    having
        logical_or(is_picked)
        and logical_and(not is_picked or result_value != event_value)
        and logical_or(not is_picked and result_value = event_value)
),

minutes_on as (
    select
        fixture_id,
        assist_player_id as player_id,
        max(minute_elapsed) as minute_on
    from {{ ref('base_apif__fixture_events') }}
    where event_type = 'subst' and assist_player_id is not null
    group by fixture_id, assist_player_id
),

minutes_settled as (
    select
        f.league_code,
        f.fixture_id,
        f.player_id,
        array_agg(
            if(
                not f.is_picked and f.minutes_played between 90 - s.minute_on and 91 - s.minute_on,
                f.minutes_played,
                null
            ) ignore nulls order by f.raw_ingested_at desc limit 1
        )[safe_offset(0)] as minutes
    from per_fetch as f
    inner join minutes_on as s
        on f.fixture_id = s.fixture_id and f.player_id = s.player_id
    group by f.league_code, f.fixture_id, f.player_id
    having logical_or(f.is_picked) and logical_and(not f.is_picked or f.minutes_played is null)
)

select
    m.league_code,
    m.fixture_id,
    m.player_id,
    'minutes' as result_name,
    m.minutes as events_count,
    b.minutes as result_value
from minutes_settled as m
inner join {{ ref('base_apif__fixture_players') }} as b
    on m.league_code = b.league_code and m.fixture_id = b.fixture_id and m.player_id = b.player_id
where m.minutes is not null and b.minutes is distinct from m.minutes

union all

select
    s.league_code,
    s.fixture_id,
    s.player_id,
    s.result_name,
    s.events_count,
    held.result_value
from settled as s
inner join {{ ref('base_apif__fixture_players') }} as b
    on s.league_code = b.league_code and s.fixture_id = b.fixture_id and s.player_id = b.player_id
cross join
    unnest([
        struct('goals' as result_name, b.goals as result_value),
        struct('assists', b.assists),
        struct('cards_yellow', b.cards_yellow),
        struct('cards_red', b.cards_red)
    ]) as held
where
    held.result_name = s.result_name
    and held.result_value is distinct from s.events_count
    and s.result_name not in (select c.stat from unnest(b.stat_corrections) as c)
