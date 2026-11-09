-- mart_player_index.order_in_nation runs 1 to n inside each nation: the national team's regulars
-- by national_team_minutes, then the others by club_order with no club last, then
-- club_minutes_this_season inside one club. Returns every player placed after one he should
-- follow, and a nation with a gap.

with pairs as (
    select
        player_sk,
        player_nationality,
        order_in_nation,
        is_national_team_regular,
        national_team_minutes,
        club_order,
        club_minutes_this_season,
        lag(is_national_team_regular) over by_order as prev_regular,
        lag(national_team_minutes) over by_order as prev_minutes,
        lag(club_order) over by_order as prev_club_order,
        lag(club_minutes_this_season) over by_order as prev_club_minutes,
        lag(order_in_nation) over by_order as prev_order
    from {{ ref('mart_player_index') }}
    window by_order as (partition by player_nationality order by order_in_nation)
)

select
    player_sk,
    'placed after a player he should precede' as failure
from pairs
where
    (not prev_regular and is_national_team_regular)
    or (prev_regular and is_national_team_regular and prev_minutes < national_team_minutes)
    or (
        not prev_regular and not is_national_team_regular
        and (
            (prev_order is not null and prev_club_order is null and club_order is not null)
            or prev_club_order > club_order
            or (prev_club_order = club_order and prev_club_minutes < club_minutes_this_season)
        )
    )

union all

select
    cast(null as int64) as player_sk,
    'order_in_nation is not 1 to n' as failure
from {{ ref('mart_player_index') }}
group by player_nationality
having max(order_in_nation) != count(*) or min(order_in_nation) != 1
