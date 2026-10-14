-- Each played match's boards on mart_leaderboards follow the Match leaders rule, recomputed here from
-- int_player_match__metrics: per board the players with a count above zero, ordered by count, then
-- fewer minutes, then player_sk; the first three kept; rank the DENSE_RANK of the count.
--
-- Returns a row (= fails) per board row on one side only, and per row whose value, rank or position
-- differs from the recomputation.
{{ config(store_failures = true) }}

{% set match_boards = [
    'shots_player', 'passes_player', 'passes_key_player', 'dribbles_attempts_player',
    'duels_won_player', 'defensive_actions_player', 'fouls_player',
] %}

with match_metrics as (
    select * from {{ ref('int_player_match__metrics') }}
),

served as (
    select
        fixture_sk,
        player_sk,
        metric_key,
        sort_value,
        rank,
        match_leader_order
    from {{ ref('mart_leaderboards') }}
    where window_type = 'match'
),

recomputed as (
    {% for key in match_boards %}
    select
        fixture_sk,
        player_sk,
        '{{ key }}' as metric_key,
        cast({{ key }} as float64) as sort_value,
        dense_rank() over (partition by fixture_sk order by {{ key }} desc) as rank,
        row_number() over (
            partition by fixture_sk
            order by {{ key }} desc, minutes asc nulls last, player_sk asc
        ) as match_leader_order
    from match_metrics
    where {{ key }} > 0
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
),

expected as (
    select * from recomputed
    where match_leader_order <= 3
)

select
    coalesce(e.fixture_sk, s.fixture_sk) as fixture_sk,
    coalesce(e.player_sk, s.player_sk) as player_sk,
    coalesce(e.metric_key, s.metric_key) as metric_key,
    e.sort_value as expected_value,
    s.sort_value as served_value,
    e.rank as expected_rank,
    s.rank as served_rank,
    e.match_leader_order as expected_order,
    s.match_leader_order as served_order
from expected as e
full outer join served as s
    on
        e.fixture_sk = s.fixture_sk
        and e.player_sk = s.player_sk
        and e.metric_key = s.metric_key
where
    e.fixture_sk is null
    or s.fixture_sk is null
    or e.sort_value != s.sort_value
    or e.rank != s.rank
    or e.match_leader_order != s.match_leader_order
