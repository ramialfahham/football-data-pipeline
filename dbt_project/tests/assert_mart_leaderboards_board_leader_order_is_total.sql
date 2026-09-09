-- board_leader_order must be a TOTAL order over a board's league leaders, and defined on nothing else.
--
-- WHY IT EXISTS. A consumer showing one leader per league orders by this column alone and compares
-- nothing itself (CPO 2026-09-09: "All ranking and ordering lives in the warehouse. The page renders
-- the order it is served"). That only holds if the column really is a total order over the leaders:
-- if two leaders on a board shared a position, the consumer's output would depend on whatever order
-- BigQuery happened to return them in, and the page would churn with no data change.
--
-- THREE INVARIANTS, and the third is the one a wrong ORDER BY breaks while the first two stay green.
--   1. Unique within a board — no two leaders share a position.
--   2. Defined exactly on the leaders — never NULL on a leader, always NULL on a non-leader.
--   3. It agrees with the RULE. Checked as an adjacency property rather than by re-deriving the
--      window: for every consecutive pair on a board, the earlier row must not be beaten by the
--      later one on the ruled keys. Re-computing `row_number()` here and comparing would be a
--      tautology - it would pass for any ORDER BY, because the test would use the same one.
--
-- ⚠ NOT scoped to a pool or a season, because the column is not. It is a global order over every
-- league leader on a board; a consumer filtering to seven leagues inherits the relative order.

with import_mart_leaderboards as (
    select * from {{ ref('mart_leaderboards') }}
),

leaders as (
    select
        metric_key,
        league_code,
        season_api_year,
        board_leader_order,
        sort_value,
        minutes,
        player_sk
    from import_mart_leaderboards
    where league_leader_order = 1
),

-- 1. Unique within a board.
duplicated_position as (
    select
        metric_key,
        board_leader_order
    from leaders
    group by metric_key, board_leader_order
    having count(*) > 1
),

-- 2. Defined on the leaders and on nothing else.
wrongly_defined as (
    select
        metric_key,
        league_code
    from import_mart_leaderboards
    where
        (league_leader_order = 1 and board_leader_order is null)
        or (league_leader_order != 1 and board_leader_order is not null)
),

-- 3. Consecutive pairs must not contradict the rule. `lead()` walks the board in the order the
--    column claims; the row that comes SECOND may not be strictly better on the ruled keys.
adjacent as (
    select
        metric_key,
        board_leader_order,
        sort_value,
        minutes,
        player_sk,
        lead(sort_value) over w as next_value,
        lead(minutes) over w as next_minutes,
        lead(player_sk) over w as next_player_sk
    from leaders
    window w as (partition by metric_key order by board_leader_order)
),

out_of_order as (
    select
        metric_key,
        board_leader_order
    from adjacent
    where
        next_value is not null
        and (
            next_value > sort_value
            -- Equal value: the later row must not have played fewer minutes. A NULL sorts last, so
            -- the later row having NULL minutes is fine; the earlier row having NULL while the
            -- later one has a number is not.
            or (
                next_value = sort_value
                and (
                    (minutes is null and next_minutes is not null)
                    or (minutes is not null and next_minutes is not null and next_minutes < minutes)
                )
            )
            -- Equal on both: the last resort must still ascend.
            or (
                next_value = sort_value
                and (minutes is not distinct from next_minutes)
                and next_player_sk < player_sk
            )
        )
)

select
    metric_key,
    cast(board_leader_order as string) as detail,
    'two leaders share a position' as failure
from duplicated_position

union all

select
    metric_key,
    league_code as detail,
    'board_leader_order defined on the wrong rows' as failure
from wrongly_defined

union all

select
    metric_key,
    cast(board_leader_order as string) as detail,
    'consecutive leaders contradict the ruled order' as failure
from out_of_order
