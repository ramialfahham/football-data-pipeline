{#
  mart_competition_fixtures — every match of a competition-season, played and unplayed, one row
  per fixture, with both teams named and linked and the round it belongs to. The competition
  page's Matchdays tab shows one competition-season of it, one round at a time; the export reads
  the table whole and groups the rows by round.

  Rounds. round_name is the provider's label. round_order is its trailing integer — a league's
  matchday; null for a named cup round. round_sequence ranks a competition-season's rounds by
  their first kick-off, the order the tab steps through them; a postponed match keeps its round,
  so a straggler played late does not move its round.

  Played. A fixture with a finished leg in int_legs__team_match — the one definition of a result
  (full time, after extra time, on penalties, or awarded), never restated here.

  is_next_round is mart_next_matchday's round, not a second derivation: every fixture of the
  round that mart serves for the competition is flagged, played or not, so this table and the Home
  page can never name different next matchdays. is_match_that_matters is that mart's flag carried
  over, false on every other row. fixture_order is the reading order of a competition-season's
  rows, rounds in sequence and each round by kick-off, so nothing downstream sorts.

  is_last_round is the round just played: in the season of the competition's next matchday (its
  current season), the latest round by round_sequence with a played fixture, and only that round's
  played fixtures. A round in progress carries both flags, its played rows this one and its unplayed
  rows is_next_round; a postponed fixture is never flagged until it is played; a competition with no
  next matchday (a finished tournament) has no current season and no flag.

  fixture_slug is the match's permanent URL segment: the kick-off date, the home team's slug,
  "-vs-", the away team's slug — the two published team slugs, so a team is spelt the same in its
  own URL and in every match URL. A fixture whose team is unknown to dim_team gets no slug and
  fails the tests, which name it, instead of the build inventing a URL.

  Grain: fixture_sk. league_code discriminates the competition and is not a BigQuery partition
  or cluster key.
#}

with fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        kickoff_datetime,
        fixture_date,
        status_short,
        goals_home,
        goals_away,
        home_team_sk,
        away_team_sk
    from {{ ref('fct_fixture') }}
),

teams as (
    select
        team_sk,
        team_name,
        team_slug,
        team_logo_url
    from {{ ref('dim_team') }}
),

played as (
    select distinct fixture_sk
    from {{ ref('int_legs__team_match') }}
),

flagged as (
    select
        fixture_sk,
        is_match_that_matters
    from {{ ref('mart_next_matchday') }}
),

next_round as (
    select distinct
        league_code,
        season_api_year,
        round_name
    from {{ ref('mart_next_matchday') }}
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

last_round as (
    select
        f.league_code,
        f.season_api_year,
        max(r.round_sequence) as round_sequence
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
    group by f.league_code, f.season_api_year
)

select
    f.fixture_sk,
    f.league_code,
    f.season_api_year,
    f.round_name,
    r.round_sequence,
    f.kickoff_datetime,
    f.fixture_date,
    f.status_short,
    f.goals_home,
    f.goals_away,
    f.home_team_sk,
    h.team_name as home_team_name,
    h.team_slug as home_team_slug,
    h.team_logo_url as home_team_logo_url,
    f.away_team_sk,
    a.team_name as away_team_name,
    a.team_slug as away_team_slug,
    a.team_logo_url as away_team_logo_url,
    safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
    p.fixture_sk is not null as is_played,
    case
        when h.team_slug is not null and a.team_slug is not null
            then concat(
                format_date('%Y-%m-%d', f.fixture_date), '-', h.team_slug, '-vs-', a.team_slug
            )
    end as fixture_slug,
    n.round_name is not null as is_next_round,
    l.league_code is not null and p.fixture_sk is not null as is_last_round,
    coalesce(m.is_match_that_matters, false) as is_match_that_matters,
    row_number() over (
        partition by f.league_code, f.season_api_year
        order by r.round_sequence asc, f.kickoff_datetime asc, f.fixture_sk asc
    ) as fixture_order
from fixtures as f
inner join rounds as r
    on
        f.league_code = r.league_code
        and f.season_api_year = r.season_api_year
        and f.round_name = r.round_name
left join teams as h
    on f.home_team_sk = h.team_sk
left join teams as a
    on f.away_team_sk = a.team_sk
left join played as p
    on f.fixture_sk = p.fixture_sk
left join flagged as m
    on f.fixture_sk = m.fixture_sk
left join next_round as n
    on
        f.league_code = n.league_code
        and f.season_api_year = n.season_api_year
        and f.round_name = n.round_name
left join last_round as l
    on
        f.league_code = l.league_code
        and f.season_api_year = l.season_api_year
        and r.round_sequence = l.round_sequence
