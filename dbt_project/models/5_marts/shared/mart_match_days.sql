{#
  mart_match_days — every match the Matches page shows, one row per fixture, with the day it falls
  on and that day's place among the page's days. The export writes one file per day from it and
  selects nothing; the site orders the competitions of a day by the site's shared order and renders
  each competition's rows in day_row_order.

  Reach. A day's matches are its competitions' last matchday (is_last_round on
  mart_competition_fixtures: the played fixtures of the round just played, in the season of the
  next matchday) and their next matchday (mart_next_matchday's rows, the same the Home page shows:
  the round of each competition's earliest fixture not yet started, its fixtures not yet started and
  dated from the build day on). A round in progress sits on both sides, its played fixtures behind
  the build day and the rest ahead. Nothing earlier and nothing later: no archive by date.

  Days. match_day is the fixture's UTC date until the venue's clock is served (#146). A day with no
  match is not a day of the page, so previous_day and next_day step over it; they are null at the
  two ends. is_opening_day marks the day the Matches page opens on: the build day when it has a
  match, else the next day that has one.

  Grain: fixture_sk. league_code discriminates the competition and is not a BigQuery partition or
  cluster key.
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
        f.fixture_date as match_day,
        f.kickoff_datetime
    from fixtures as f
    left join next_matchday as n
        on f.fixture_sk = n.fixture_sk
    where f.is_last_round or n.fixture_sk is not null
),

days as (
    select distinct match_day
    from in_reach
),

day_links as (
    select
        match_day,
        lag(match_day) over (order by match_day asc) as previous_day,
        lead(match_day) over (order by match_day asc) as next_day,
        match_day = min(if(match_day >= current_date(), match_day, null)) over () as is_opening_day
    from days
)

select
    r.fixture_sk,
    r.league_code,
    r.match_day,
    d.previous_day,
    d.next_day,
    row_number() over (
        partition by r.match_day, r.league_code
        order by r.kickoff_datetime asc, r.fixture_sk asc
    ) as day_row_order,
    coalesce(d.is_opening_day, false) as is_opening_day
from in_reach as r
inner join day_links as d
    on r.match_day = d.match_day
