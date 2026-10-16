-- A team sheet is numbered 1 to n: every starter, then the substitutes who came on in the order
-- they came on, then the substitutes who did not. Returns a row (= fails) per team sheet whose
-- lineup_order skips, repeats or breaks that order.
{{ config(store_failures = true) }}

with sheet as (
    select
        fixture_sk,
        team_sk,
        is_starter,
        lineup_order,
        not is_starter and minute_on is not null as came_on,
        not is_starter and minute_on is null as stayed_on_bench,
        minute_on * 100 + coalesce(minute_on_extra, 0) as minute_on_key
    from {{ ref('fct_fixture_lineup') }}
),

stepped as (
    select
        *,
        lag(minute_on_key) over (
            partition by fixture_sk, team_sk, came_on
            order by lineup_order
        ) as previous_minute_on_key
    from sheet
)

select
    fixture_sk,
    team_sk,
    count(*) as n_players,
    min(lineup_order) as first_order,
    max(lineup_order) as last_order
from stepped
group by fixture_sk, team_sk
having
    min(lineup_order) != 1
    or max(lineup_order) != count(*)
    or count(distinct lineup_order) != count(*)
    or max(if(is_starter, lineup_order, null)) > min(if(not is_starter, lineup_order, null))
    or max(if(came_on, lineup_order, null)) > min(if(stayed_on_bench, lineup_order, null))
    or countif(came_on and minute_on_key < previous_minute_on_key) > 0
