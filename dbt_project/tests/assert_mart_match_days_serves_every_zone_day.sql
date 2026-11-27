-- Every match on the Matches page is served on exactly the days the site's time zones, UTC-12 to
-- UTC+14, put it on: its UTC date, flagged is_utc_day, and the dates of its kick-off 12 hours
-- earlier and 14 hours later, each once; and each day's rows of a competition run in kick-off
-- order. Recomputed from the kick-off on mart_competition_fixtures, so a rewrite that drops a
-- neighbouring day, adds one no zone reaches, or orders a day's rows off the clock fails here.
--
-- Returns a row (= fails) per fixture and day where a property does not hold.
{{ config(store_failures = true) }}

with served as (
    select
        d.fixture_sk,
        d.league_code,
        d.match_day,
        d.is_utc_day,
        d.day_row_order,
        c.fixture_date,
        c.kickoff_datetime
    from {{ ref('mart_match_days') }} as d
    inner join {{ ref('mart_competition_fixtures') }} as c
        on d.fixture_sk = c.fixture_sk
),

expected as (
    select distinct
        s.fixture_sk,
        match_day,
        match_day = s.fixture_date as is_utc_day
    from served as s
    cross join
        unnest([
            s.fixture_date,
            date(timestamp_sub(s.kickoff_datetime, interval 12 hour)),
            date(timestamp_add(s.kickoff_datetime, interval 14 hour))
        ]) as match_day
    where match_day is not null
),

served_days as (
    select distinct
        fixture_sk,
        match_day,
        is_utc_day
    from served
),

day_set as (
    select
        coalesce(s.fixture_sk, e.fixture_sk) as fixture_sk,
        coalesce(s.match_day, e.match_day) as match_day,
        'day set' as failure
    from served_days as s
    full outer join expected as e
        on
            s.fixture_sk = e.fixture_sk
            and s.match_day = e.match_day
            and s.is_utc_day = e.is_utc_day
    where s.fixture_sk is null or e.fixture_sk is null
),

out_of_order as (
    select
        fixture_sk,
        match_day,
        'kick-off order' as failure
    from served
    qualify day_row_order != row_number() over (
        partition by match_day, league_code
        order by kickoff_datetime asc, fixture_sk asc
    )
),

duplicated as (
    select
        fixture_sk,
        match_day,
        'duplicate row' as failure
    from served
    group by fixture_sk, match_day
    having count(*) > 1
)

select * from day_set
union all
select * from out_of_order
union all
select * from duplicated
