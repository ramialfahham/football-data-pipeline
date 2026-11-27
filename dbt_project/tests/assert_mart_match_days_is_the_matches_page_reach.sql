-- mart_match_days holds exactly the Matches page's reach and its days: each competition's last
-- matchday (the played fixtures of the latest round with a played fixture, in the season of its
-- earliest fixture not yet started) and its next matchday (the not-yet-started fixtures, dated from
-- the build day on, of the round of that earliest fixture), each on its UTC date; every served day
-- names as its neighbours the adjacent days a match reaches in some time zone; the opening day is
-- the first day from the build day on with a match on its UTC date; and no day before the build day
-- holds an unplayed fixture on its UTC date.
--
-- Recomputed from fct_fixture and int_legs__team_match, not from either mart, so a rewrite that
-- lets in a past unplayed fixture, a next-matchday fixture dated in the past, opens on the first day
-- overall, or links a day past a neighbour with a match fails here even when the schema tests stay
-- green.
--
-- Returns a row (= fails) per fixture and day where any property does not hold.
{{ config(store_failures = true) }}

with fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        status_short,
        fixture_date,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
),

played as (
    select distinct fixture_sk
    from {{ ref('int_legs__team_match') }}
),

upcoming as (
    select *
    from fixtures
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

next_round as (
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

next_rows as (
    select u.fixture_sk
    from upcoming as u
    inner join next_round as n
        on
            u.league_code = n.league_code
            and u.season_api_year = n.season_api_year
            and u.round_name = n.round_name
),

rounds as (
    select
        league_code,
        season_api_year,
        round_name,
        dense_rank() over (
            partition by league_code, season_api_year
            order by min(kickoff_datetime) asc, round_name asc
        ) as round_sequence
    from fixtures
    group by league_code, season_api_year, round_name
),

season_played as (
    select
        f.fixture_sk,
        f.league_code,
        r.round_sequence
    from fixtures as f
    inner join next_round as n
        on
            f.league_code = n.league_code
            and f.season_api_year = n.season_api_year
    inner join played as p
        on f.fixture_sk = p.fixture_sk
    inner join rounds as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
),

last_rows as (
    select fixture_sk
    from season_played
    qualify round_sequence = max(round_sequence) over (partition by league_code)
),

expected as (
    select
        f.fixture_sk,
        f.fixture_date as match_day,
        f.kickoff_datetime
    from fixtures as f
    where
        f.fixture_sk in (select n.fixture_sk from next_rows as n)
        or f.fixture_sk in (select l.fixture_sk from last_rows as l)
),

expected_all_days as (
    select
        match_day,
        logical_or(is_utc_day) as has_utc_match
    from (
        select
            match_day,
            true as is_utc_day
        from expected
        union all
        select
            date(timestamp_sub(kickoff_datetime, interval 12 hour)) as match_day,
            false as is_utc_day
        from expected
        union all
        select
            date(timestamp_add(kickoff_datetime, interval 14 hour)) as match_day,
            false as is_utc_day
        from expected
    )
    where match_day is not null
    group by match_day
),

expected_days as (
    select
        match_day,
        lag(match_day) over (order by match_day asc) as previous_day,
        lead(match_day) over (order by match_day asc) as next_day,
        match_day = min(if(match_day >= current_date() and has_utc_match, match_day, null)) over ()
            as is_opening_day
    from expected_all_days
),

served as (
    select
        fixture_sk,
        match_day,
        is_utc_day,
        previous_day,
        next_day,
        is_opening_day
    from {{ ref('mart_match_days') }}
),

served_utc_days as (
    select
        fixture_sk,
        match_day
    from served
    where is_utc_day
),

out_of_reach as (
    select
        s.match_day,
        e.match_day as expected_day,
        coalesce(s.fixture_sk, e.fixture_sk) as fixture_sk,
        'reach' as failure
    from served_utc_days as s
    full outer join expected as e
        on s.fixture_sk = e.fixture_sk
    left join played as p
        on coalesce(s.fixture_sk, e.fixture_sk) = p.fixture_sk
    where
        s.fixture_sk is null
        or e.fixture_sk is null
        or s.match_day != e.match_day
        or (s.match_day < current_date() and p.fixture_sk is null)
),

wrong_day_facts as (
    select
        s.match_day,
        d.match_day as expected_day,
        s.fixture_sk,
        'day facts' as failure
    from served as s
    left join expected_days as d
        on s.match_day = d.match_day
    where
        d.match_day is null
        or s.previous_day is distinct from d.previous_day
        or s.next_day is distinct from d.next_day
        or s.is_opening_day != coalesce(d.is_opening_day, false)
)

select * from out_of_reach
union all
select * from wrong_day_facts
