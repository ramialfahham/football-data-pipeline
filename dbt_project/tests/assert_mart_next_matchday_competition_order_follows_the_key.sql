-- competition_order is exactly "the competitions in the ruled order": one value per competition,
-- one competition per value, and the value is the competition's place by the day its matchday
-- starts, then its region rank (Europe first), then its earliest kick-off, then league_code.
--
-- Recomputed from the mart's rows and the two seeds, not from the mart's CTEs, so a rewrite that
-- orders by another key, skips a place or gives one competition two places fails here even when
-- the not_null test stays green.
--
-- Returns a row (= fails) per competition where the property does not hold.
{{ config(store_failures = true) }}

with served as (
    select
        league_code,
        count(distinct competition_order) as n_orders,
        min(competition_order) as competition_order,
        min(fixture_date) as first_date,
        min(kickoff_datetime) as first_kickoff
    from {{ ref('mart_next_matchday') }}
    group by league_code
),

expected as (
    select
        s.league_code,
        s.n_orders,
        s.competition_order,
        dense_rank() over (
            order by
                s.first_date asc,
                c.region_rank asc nulls last,
                s.first_kickoff asc nulls last,
                s.league_code asc
        ) as expected_order,
        count(*) over (partition by s.competition_order) as n_competitions_at_order
    from served as s
    left join {{ ref('competition_registry') }} as r
        on s.league_code = r.league_code
    left join {{ ref('confederations') }} as c
        on r.confederation = c.confederation
)

select
    league_code,
    n_orders,
    competition_order,
    expected_order,
    n_competitions_at_order
from expected
where
    n_orders != 1
    or competition_order != expected_order
    or n_competitions_at_order != 1
