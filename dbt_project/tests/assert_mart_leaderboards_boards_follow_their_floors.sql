-- Who enters a season board of mart_leaderboards (the ranking_rules doc block), checked against the
-- player's season row in int_player_season__metrics. Fail a per-90 or percentage row under the
-- minutes floor, a percentage row under its attempts floor, a goalkeeper on an outfield board, an
-- outfield player on the goals-against board, a zero on a most-first board, and a missing season
-- board (the board set is the Statistics and Rankings tab player boards, 44 of them).
{{ config(store_failures = true) }}

{% set attempts = {
    'shots_on_goal_player_pct': ('shots_player', 'player_min_shots'),
    'dribbles_success_player_pct': ('dribbles_attempts_player', 'player_min_dribbles'),
    'duels_won_player_pct': ('duels_player', 'player_min_duels'),
    'saves_player_pct': ('shots_on_goal_against_player', 'player_min_shots_on_target_faced'),
    'finishing_efficiency_player_pct': ('shots_on_goal_player', 'player_min_shots_on_target'),
} %}
{% set outfield_boards = ['passes_accuracy_player_pct', 'finishing_efficiency_player_pct'] %}

with served as (
    select
        l.metric_key,
        l.player_sk,
        l.season_sk,
        l.rank_order,
        l.sort_value,
        p.player_position,
        s.minutes,
        s.shots_player,
        s.dribbles_attempts_player,
        s.duels_player,
        s.shots_on_goal_against_player,
        s.shots_on_goal_player
    from {{ ref('mart_leaderboards') }} as l
    inner join {{ ref('int_player_season__metrics') }} as s
        on l.player_sk = s.player_sk and l.season_sk = s.season_sk
    left join {{ ref('dim_player') }} as p
        on l.player_sk = p.player_sk
    where l.window_type = 'season_to_date'
),

violations as (
    select
        metric_key,
        player_sk,
        season_sk,
        'under the minutes floor' as failure
    from served
    where
        (metric_key like '%\\_per90' or metric_key like '%\\_pct')
        and not coalesce(minutes >= {{ var('player_min_minutes') }}, false)

    {% for key, floor in attempts.items() %}
    union all
    select
        metric_key,
        player_sk,
        season_sk,
        'under the attempts floor' as failure
    from served
    where metric_key = '{{ key }}' and not coalesce({{ floor[0] }} >= {{ var(floor[1]) }}, false)
    {% endfor %}

    union all
    select
        metric_key,
        player_sk,
        season_sk,
        'not an outfield player on an outfield board' as failure
    from served
    where
        metric_key in (
            {% for key in outfield_boards %}
            '{{ key }}'{% if not loop.last %},{% endif %}
            {% endfor %}
        )
        and not coalesce(player_position != 'Goalkeeper', false)

    union all
    select
        metric_key,
        player_sk,
        season_sk,
        'not a goalkeeper on the goals-against board' as failure
    from served
    where metric_key = 'goals_against_per90' and not coalesce(player_position = 'Goalkeeper', false)

    union all
    select
        metric_key,
        player_sk,
        season_sk,
        'a zero on a most-first board' as failure
    from served
    where rank_order = 'desc' and not sort_value > 0
),

board_count as (
    select count(distinct metric_key) as boards
    from {{ ref('mart_leaderboards') }}
    where window_type = 'season_to_date'
)

select * from violations
union all
select
    cast(boards as string) as metric_key,
    cast(null as int64) as player_sk,
    cast(null as string) as season_sk,
    'the season board set is not 44 boards' as failure
from board_count
where boards != 44
