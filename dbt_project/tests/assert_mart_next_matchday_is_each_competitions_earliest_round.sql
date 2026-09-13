-- mart_next_matchday is exactly "each competition's next round, whole": for every competition
-- with an upcoming fixture in fct_fixture, the mart holds ONE round, it is the round of that
-- competition's earliest upcoming fixture, and every upcoming fixture of that round is in it.
--
-- Checked against fct_fixture rather than against the mart's own CTEs, so a rewrite of the mart
-- that drifts from the definition (a calendar-day window, a cap, a round chosen by anything but
-- the earliest date) fails here even when the mart's schema tests stay green.
--
-- Returns a row (= fails) per competition where any of the three properties does not hold.
with upcoming as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        fixture_date,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

expected_round as (
    select
        league_code,
        season_api_year,
        round_name
    from upcoming
    qualify row_number() over (
        partition by league_code
        order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
    ) = 1
),

expected_rows as (
    select
        u.league_code,
        count(*) as n_expected
    from upcoming as u
    inner join expected_round as e
        on
            u.league_code = e.league_code
            and u.season_api_year = e.season_api_year
            and u.round_name = e.round_name
    group by u.league_code
),

served as (
    select
        league_code,
        count(distinct round_name) as n_rounds,
        min(round_name) as served_round,
        count(*) as n_served
    from {{ ref('mart_next_matchday') }}
    group by league_code
)

select
    e.league_code,
    e.round_name as expected_round,
    s.served_round,
    s.n_rounds,
    x.n_expected,
    s.n_served
from expected_round as e
inner join expected_rows as x
    on e.league_code = x.league_code
left join served as s
    on e.league_code = s.league_code
where
    s.league_code is null
    or s.n_rounds != 1
    or s.served_round != e.round_name
    or s.n_served != x.n_expected
