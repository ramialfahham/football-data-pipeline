{#
  mart_match_days — every match the Matches page shows, one row per match and day it can fall on,
  with that day's place among the page's days. The export writes one file per day from it and
  selects nothing; the site orders the competitions of a day by the site's shared order and renders
  each competition's rows in day_row_order, showing those the fan's time zone puts on the day.

  Reach. The page's matches are each competition's last matchday (is_last_round on
  mart_competition_fixtures: the played fixtures of the round just played, in the season of the
  next matchday) and its next matchday (mart_next_matchday's rows, the same the Home page shows:
  the round of the competition's earliest fixture not yet started, its fixtures not yet started and
  dated from the build day on). By UTC date a round in progress sits on both sides, its played
  fixtures behind the build day and the rest ahead. Nothing earlier and nothing later: no archive
  by date.

  Days. The site's time zones run from UTC-12 to UTC+14, so a match falls on its UTC date and, in
  some zone, on the dates of its kick-off 12 hours earlier and 14 hours later. It has a row on each;
  is_utc_day marks its UTC date, the day the page shows it on without a zone. Every such day is a
  day of the page, so previous_day and next_day step over a day no match reaches; they are null at
  the two ends. is_opening_day marks the day the Matches page opens on: the build day when a match
  falls on it by UTC, else the next day one does.

  Grain: (match_day, fixture_sk). league_code discriminates the competition and is not a BigQuery
  partition or cluster key.
#}

with fixtures as (
    select
        fixture_sk,
        league_code,
        fixture_date,
        kickoff_datetime,
        is_last_round
    from {{ ref('mart_competition_fixtures') }}
),

next_matchday as (
    select fixture_sk
    from {{ ref('mart_next_matchday') }}
),

in_reach as (
    select
        f.fixture_sk,
        f.league_code,
        f.fixture_date,
        f.kickoff_datetime
    from fixtures as f
    left join next_matchday as n
        on f.fixture_sk = n.fixture_sk
    where f.is_last_round or n.fixture_sk is not null
),

zone_days as (
    select distinct
        r.fixture_sk,
        r.league_code,
        r.kickoff_datetime,
        match_day,
        match_day = r.fixture_date as is_utc_day
    from in_reach as r
    cross join
        unnest([
            r.fixture_date,
            date(timestamp_sub(r.kickoff_datetime, interval 12 hour)),
            date(timestamp_add(r.kickoff_datetime, interval 14 hour))
        ]) as match_day
    where match_day is not null
),

days as (
    select
        match_day,
        logical_or(is_utc_day) as has_utc_match
    from zone_days
    group by match_day
),

day_links as (
    select
        match_day,
        lag(match_day) over (order by match_day asc) as previous_day,
        lead(match_day) over (order by match_day asc) as next_day,
        match_day = min(if(match_day >= current_date() and has_utc_match, match_day, null)) over ()
            as is_opening_day
    from days
)

select
    z.fixture_sk,
    z.league_code,
    z.match_day,
    z.is_utc_day,
    d.previous_day,
    d.next_day,
    row_number() over (
        partition by z.match_day, z.league_code
        order by z.kickoff_datetime asc, z.fixture_sk asc
    ) as day_row_order,
    coalesce(d.is_opening_day, false) as is_opening_day
from zone_days as z
inner join day_links as d
    on z.match_day = d.match_day
