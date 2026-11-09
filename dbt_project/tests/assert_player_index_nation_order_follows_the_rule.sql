-- mart_player_index.nation_order: one value per nation, 1 to n over the nations, the nations by
-- their national team's national_team_rank in mart_team_index, a shared rank by name, then the
-- nations without one A to Z, then no nationality last. Returns every nation out of that order, a
-- nation with two orders or a wrong rank, and a gap.

with rows_ as (
    select
        p.player_nationality,
        p.nation_order,
        p.national_team_rank,
        t.national_team_rank as index_rank
    from {{ ref('mart_player_index') }} as p
    left join {{ ref('mart_team_index') }} as t
        on p.nationality_team_sk = t.team_sk
),

nations as (
    select
        player_nationality,
        min(nation_order) as nation_order,
        min(national_team_rank) as national_team_rank,
        count(distinct nation_order) as orders,
        countif(national_team_rank is distinct from index_rank) as wrong_ranks
    from rows_
    group by player_nationality
),

pairs as (
    select
        *,
        lag(player_nationality) over by_order as prev_nationality,
        lag(national_team_rank) over by_order as prev_rank,
        lag(nation_order) over by_order as prev_order
    from nations
    window by_order as (order by nation_order)
)

select
    player_nationality,
    'out of order, two orders or a wrong rank' as failure
from pairs
where
    orders != 1
    or wrong_ranks > 0
    or prev_order = nation_order
    or (prev_order is not null and prev_nationality is null)
    or (prev_rank is null and national_team_rank is not null and prev_order is not null)
    or prev_rank > national_team_rank
    or (prev_rank = national_team_rank and prev_nationality > player_nationality)
    or (prev_rank is null and national_team_rank is null and prev_nationality > player_nationality)

union all

select
    cast(null as string) as player_nationality,
    'nation_order is not 1 to n' as failure
from (
    select
        min(nation_order) as first_order,
        max(nation_order) as last_order,
        count(*) as nations
    from nations
)
where first_order != 1 or last_order != nations
