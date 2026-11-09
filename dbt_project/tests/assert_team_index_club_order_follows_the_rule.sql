-- mart_team_index.club_order runs 1 to n over the clubs: the clubs with a top_club_rank first, by
-- region_rank then that rank, then the others by country_order and, inside a country,
-- team_order_in_country. Returns every club placed after one it should precede, and a gap.

with clubs as (
    select
        team_sk,
        club_order,
        top_club_rank,
        country_order,
        team_country,
        team_order_in_country,
        top_club_rank is not null as is_ranked,
        coalesce(region_rank, 1000) as region_place
    from {{ ref('mart_team_index') }}
    where entity_type = 'club'
),

pairs as (
    select
        *,
        lag(is_ranked) over by_order as prev_is_ranked,
        lag(region_place) over by_order as prev_region_place,
        lag(top_club_rank) over by_order as prev_top_club_rank,
        lag(country_order) over by_order as prev_country_order,
        lag(team_country) over by_order as prev_team_country,
        lag(team_order_in_country) over by_order as prev_team_order_in_country
    from clubs
    window by_order as (order by club_order)
)

select
    team_sk,
    'placed after a club it should precede' as failure
from pairs
where
    (not prev_is_ranked and is_ranked)
    or (
        prev_is_ranked and is_ranked
        and (
            prev_region_place > region_place
            or (prev_region_place = region_place and prev_top_club_rank > top_club_rank)
        )
    )
    or (
        not prev_is_ranked and not is_ranked
        and (
            prev_country_order > country_order
            or (
                prev_country_order = country_order
                and prev_team_country is not distinct from team_country
                and prev_team_order_in_country > team_order_in_country
            )
        )
    )

union all

select
    cast(null as int64) as team_sk,
    'club_order is not 1 to n' as failure
from (
    select
        min(club_order) as first_order,
        max(club_order) as last_order,
        count(*) as clubs
    from clubs
)
where first_order != 1 or last_order != clubs
