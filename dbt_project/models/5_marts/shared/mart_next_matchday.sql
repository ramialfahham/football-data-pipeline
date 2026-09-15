{#
  mart_next_matchday — every competition's next matchday: one row per upcoming fixture in the
  round of that competition's earliest fixture not yet started. The Home page's Next matches
  block reads it whole; the export filters nothing and decides nothing (GAP-32 closed here —
  the matchday used to be chosen in the export's own query).

  "Upcoming" is a scheduled status (NS / TBD) AND a date on or after the build day: a fixture
  the provider never advanced past NS but dated in the past is not a next matchday. The build
  is nightly, so the table is correct as of the morning it was built and the export runs after
  it in the same run.

  A postponed match keeps its original round name, so between a round's end and its
  rescheduled straggler the competition's next matchday is that one match. That is the ruled
  definition; the straggler counts and the alternative are on GitLab #143.

  Every competition with an upcoming fixture is present, cups and tournaments alike; nothing is
  capped and nothing is ordered here — the page applies the site-wide competition ordering key
  and folds rows past the third. league_code discriminates the competition and is not a
  BigQuery partition or cluster key.

  is_match_that_matters flags, per competition, the fixture of the matchday whose two teams
  have the lowest sum of table positions (1st v 9th beats 5th v 7th); ties go to the earlier
  kickoff, then fixture_sk. A team's position is its rank in the one standings section it
  belongs to that season; a team in several sections (a split season) or in none has no
  position, and a fixture with a missing position is never flagged, so a knockout round has no
  flag. Chosen here, not in the export: which match matters is a ranking, and rankings live in
  the warehouse.

  Grain: fixture_sk.
#}

with upcoming as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        kickoff_datetime,
        fixture_date,
        status_short,
        home_team_sk,
        away_team_sk
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

-- The round of each competition's earliest upcoming fixture; kickoff then fixture_sk break a
-- same-day tie deterministically (the round is the same either way on a normal matchday).
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

next_matchday as (
    select
        u.fixture_sk,
        u.league_code,
        u.season_api_year,
        u.round_name,
        u.kickoff_datetime,
        u.fixture_date,
        u.status_short,
        u.home_team_sk,
        u.away_team_sk
    from upcoming as u
    inner join next_round as n
        on
            u.league_code = n.league_code
            and u.season_api_year = n.season_api_year
            and u.round_name = n.round_name
),

-- A team's table position, only where it sits in exactly one standings section that season.
positions as (
    select
        league_code,
        season_api_year,
        team_sk,
        standing_rank
    from {{ ref('fct_standings') }}
    qualify count(*) over (partition by league_code, season_api_year, team_sk) = 1
),

ranked as (
    select
        m.fixture_sk,
        m.league_code,
        m.season_api_year,
        m.round_name,
        m.kickoff_datetime,
        m.fixture_date,
        m.status_short,
        m.home_team_sk,
        m.away_team_sk,
        h.standing_rank + a.standing_rank as position_sum
    from next_matchday as m
    left join positions as h
        on
            m.league_code = h.league_code
            and m.season_api_year = h.season_api_year
            and m.home_team_sk = h.team_sk
    left join positions as a
        on
            m.league_code = a.league_code
            and m.season_api_year = a.season_api_year
            and m.away_team_sk = a.team_sk
)

select
    fixture_sk,
    league_code,
    season_api_year,
    round_name,
    kickoff_datetime,
    fixture_date,
    status_short,
    home_team_sk,
    away_team_sk,
    coalesce(
        position_sum is not null
        and row_number() over (
            partition by league_code, (position_sum is null)
            order by position_sum asc, fixture_date asc, kickoff_datetime asc, fixture_sk asc
        ) = 1,
        false
    ) as is_match_that_matters
from ranked
