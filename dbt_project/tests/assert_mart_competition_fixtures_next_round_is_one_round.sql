-- is_next_round on mart_competition_fixtures is exactly mart_next_matchday's round, whole: for a
-- competition with an upcoming fixture in fct_fixture the flag sits on one (season, round), it is
-- the round of that competition's earliest fixture not yet started — the rule mart_next_matchday
-- applies, league-wide, not per season — and it sits on every fixture of that round, played or
-- not; a competition with no upcoming fixture has no flag; and every fixture mart_next_matchday
-- serves is flagged, so the two marts never disagree on the next matchday.
--
-- Recomputed from fct_fixture, not from either mart's CTEs, so a rewrite that flags per season,
-- flags two rounds, flags a round's unplayed fixtures only, or flags by a calendar window fails
-- here even when the schema tests stay green.
--
-- Returns a row (= fails) per competition where any property does not hold.
{{ config(store_failures = true) }}

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
        f.league_code,
        count(*) as n_expected
    from {{ ref('fct_fixture') }} as f
    inner join expected_round as e
        on
            f.league_code = e.league_code
            and f.season_api_year = e.season_api_year
            and f.round_name = e.round_name
    group by f.league_code
),

served as (
    select
        league_code,
        count(distinct if(is_next_round, concat(season_api_year, ' ', round_name), null)) as n_rounds,
        min(if(is_next_round, season_api_year, null)) as served_season,
        min(if(is_next_round, round_name, null)) as served_round,
        countif(is_next_round) as n_served
    from {{ ref('mart_competition_fixtures') }}
    group by league_code
),

home_page_rows as (
    select
        n.league_code,
        countif(not coalesce(c.is_next_round, false)) as n_unflagged
    from {{ ref('mart_next_matchday') }} as n
    left join {{ ref('mart_competition_fixtures') }} as c
        on n.fixture_sk = c.fixture_sk
    group by n.league_code
)

select
    s.league_code,
    e.season_api_year as expected_season,
    e.round_name as expected_round,
    s.served_season,
    s.served_round,
    s.n_rounds,
    x.n_expected,
    s.n_served,
    coalesce(h.n_unflagged, 0) as n_home_page_rows_unflagged
from served as s
left join expected_round as e
    on s.league_code = e.league_code
left join expected_rows as x
    on s.league_code = x.league_code
left join home_page_rows as h
    on s.league_code = h.league_code
where
    (e.round_name is null and s.n_served != 0)
    or (
        e.round_name is not null
        and (
            s.n_rounds != 1
            or s.served_season != e.season_api_year
            or s.served_round != e.round_name
            or s.n_served != x.n_expected
        )
    )
    or coalesce(h.n_unflagged, 0) != 0
