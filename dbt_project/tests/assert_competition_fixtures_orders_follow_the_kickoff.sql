-- Both served orders of mart_competition_fixtures follow the kick-off instant: kickoff_order over
-- every match, and fixture_order inside each competition-season's round. A page files a round, or a
-- list across competitions, under the days of the fan's time zone in these orders, so an order
-- taken from the venue's clock, or from anything else, would put a day heading out of date order.
--
-- Returns a row (= fails) per fixture that kicks off before the fixture ordered just ahead of it.
{{ config(store_failures = true) }}

with fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_sequence,
        kickoff_datetime,
        fixture_order,
        kickoff_order
    from {{ ref('mart_competition_fixtures') }}
),

stepped as (
    select
        fixture_sk,
        kickoff_datetime,
        lag(kickoff_datetime) over (order by kickoff_order asc) as ahead_by_kickoff_order,
        lag(kickoff_datetime) over (
            partition by league_code, season_api_year, round_sequence
            order by fixture_order asc
        ) as ahead_in_round
    from fixtures
)

select
    fixture_sk,
    'kickoff_order' as failure
from stepped
where kickoff_datetime < ahead_by_kickoff_order
union all
select
    fixture_sk,
    'fixture_order' as failure
from stepped
where kickoff_datetime < ahead_in_round
