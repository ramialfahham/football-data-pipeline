-- mart_player_index's Players page flags against a recount: a player shows under his nation when he
-- is a regular or at most 10 other players of the nation come before him or at his place in
-- order_in_nation, and the same inside his position; a nation with a nationality has a page when
-- the page leaves one of its players out, the same value on every row. Returns every player whose
-- flag differs.

with players as (
    select
        player_sk,
        player_nationality,
        position_group,
        order_in_nation,
        is_national_team_regular,
        is_hub_shown,
        is_hub_shown_in_position,
        has_nation_page
    from {{ ref('mart_player_index') }}
),

others_before as (
    select
        a.player_sk,
        countif(not b.is_national_team_regular) as others_up_to_me,
        countif(
            not b.is_national_team_regular
            and b.position_group = a.position_group
        ) as position_others_up_to_me
    from players as a
    inner join players as b
        on
            a.player_nationality is not distinct from b.player_nationality
            and a.order_in_nation >= b.order_in_nation
    group by a.player_sk
),

expected as (
    select
        p.player_sk,
        p.player_nationality,
        p.is_hub_shown,
        p.is_hub_shown_in_position,
        p.has_nation_page,
        p.is_national_team_regular or o.others_up_to_me <= 10 as shown,
        p.position_group is not null
        and (p.is_national_team_regular or o.position_others_up_to_me <= 10) as shown_in_position
    from players as p
    inner join others_before as o
        on p.player_sk = o.player_sk
),

nations as (
    select
        player_nationality,
        player_nationality is not null and logical_or(not shown) as page,
        count(distinct has_nation_page) as values_held
    from expected
    group by player_nationality
)

select e.player_sk
from expected as e
inner join nations as n
    on e.player_nationality is not distinct from n.player_nationality
where
    e.is_hub_shown != e.shown
    or e.is_hub_shown_in_position != e.shown_in_position
    or e.has_nation_page != n.page
    or n.values_held != 1
