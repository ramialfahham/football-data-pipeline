{{ config(materialized='table') }}

{#
  mart_competition_season_summary — one row per competition-season with the season's headline
  numbers: how many matches and goals, goals per match, how results split between home wins,
  away wins and draws, the match with the biggest margin, the match with the most goals, and the
  longest unbeaten and winless runs of the season with the teams that hold them.

  Built over the finished legs of int_legs__team_match (the one definition of a finished match,
  both scores known), so every count here reconciles with the team-season rollups. These are
  tallies of match results at competition grain, not catalogue metrics: no team or player is
  being measured, and a page renders them as facts of the season next to the table.

  A tie on the biggest margin goes to the match with more goals, a tie on the most goals to the
  match with the bigger margin; what is still tied goes to the earlier kickoff, and the fixture
  id decides only when two matches share all three. A run is the longest unbroken stretch of the season for a team, ordered by
  kickoff — not the run it is on at the moment, which the team profile carries separately — and
  the arrays hold every team that shares the longest one, in team_sk order. A run of one match
  is not a run: until some team has strung two together the run is NULL and its holders empty,
  so a page shows no "longest run" held by every team after the first round.

  Home and away wins are NULL for national-team competitions: their matches are mostly played at
  neutral venues, where the provider's "home" side is an administrative label, and a count of
  home wins would be a number nobody means. league_code discriminates the competition and is
  not a BigQuery partition or cluster key.

  Grain: (league_code, season_api_year).
#}

with legs as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        team_sk,
        home_away,
        kickoff_datetime,
        round_name,
        goals_for,
        goals_against,
        result,
        competition_type,
        entity_type
    from {{ ref('int_legs__team_match') }}
),

-- One row per finished match, seen from the home side.
matches as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        team_sk as home_team_sk,
        goals_for as goals_home,
        goals_against as goals_away,
        result as home_result,
        competition_type,
        entity_type
    from legs
    where home_away = 'home'
),

away_sides as (
    select
        fixture_sk,
        team_sk as away_team_sk
    from legs
    where home_away = 'away'
),

season_totals as (
    select
        league_code,
        season_api_year,
        any_value(competition_type) as competition_type,
        any_value(entity_type) as entity_type,
        count(*) as matches_played,
        sum(goals_home + goals_away) as total_goals,
        countif(home_result = 'W') as home_wins,
        countif(home_result = 'L') as away_wins,
        countif(home_result = 'D') as drawn_matches
    from matches
    group by league_code, season_api_year
),

biggest_margin as (
    select
        m.league_code,
        m.season_api_year,
        m.fixture_sk,
        m.home_team_sk,
        a.away_team_sk,
        m.goals_home,
        m.goals_away,
        m.round_name,
        m.kickoff_datetime
    from matches as m
    inner join away_sides as a
        on m.fixture_sk = a.fixture_sk
    qualify row_number() over (
        partition by m.league_code, m.season_api_year
        order by
            abs(m.goals_home - m.goals_away) desc,
            m.goals_home + m.goals_away desc,
            m.kickoff_datetime asc,
            m.fixture_sk asc
    ) = 1
),

most_goals as (
    select
        m.league_code,
        m.season_api_year,
        m.fixture_sk,
        m.home_team_sk,
        a.away_team_sk,
        m.goals_home,
        m.goals_away,
        m.round_name,
        m.kickoff_datetime
    from matches as m
    inner join away_sides as a
        on m.fixture_sk = a.fixture_sk
    qualify row_number() over (
        partition by m.league_code, m.season_api_year
        order by
            m.goals_home + m.goals_away desc,
            abs(m.goals_home - m.goals_away) desc,
            m.kickoff_datetime asc,
            m.fixture_sk asc
    ) = 1
),

-- Gaps and islands: a run's island id is the count of run-breaking results up to and including
-- this match, so every match after a break starts a new island.
ordered_legs as (
    select
        league_code,
        season_api_year,
        team_sk,
        result,
        countif(result = 'L') over (
            partition by league_code, season_api_year, team_sk
            order by kickoff_datetime, fixture_sk
            rows between unbounded preceding and current row
        ) as loss_island,
        countif(result = 'W') over (
            partition by league_code, season_api_year, team_sk
            order by kickoff_datetime, fixture_sk
            rows between unbounded preceding and current row
        ) as win_island
    from legs
),

unbeaten_islands as (
    select
        league_code,
        season_api_year,
        team_sk,
        countif(result != 'L') as run_length
    from ordered_legs
    group by league_code, season_api_year, team_sk, loss_island
),

winless_islands as (
    select
        league_code,
        season_api_year,
        team_sk,
        countif(result != 'W') as run_length
    from ordered_legs
    group by league_code, season_api_year, team_sk, win_island
),

team_longest as (
    select
        u.league_code,
        u.season_api_year,
        u.team_sk,
        max(u.run_length) as longest_unbeaten,
        max(w.run_length) as longest_winless
    from unbeaten_islands as u
    inner join winless_islands as w
        on
            u.league_code = w.league_code
            and u.season_api_year = w.season_api_year
            and u.team_sk = w.team_sk
    group by u.league_code, u.season_api_year, u.team_sk
),

league_runs as (
    select
        league_code,
        season_api_year,
        max(longest_unbeaten) as longest_unbeaten_run,
        array_agg(
            if(longest_unbeaten = max_unbeaten, team_sk, null) ignore nulls order by team_sk
        ) as longest_unbeaten_team_sks,
        max(longest_winless) as longest_winless_run,
        array_agg(
            if(longest_winless = max_winless, team_sk, null) ignore nulls order by team_sk
        ) as longest_winless_team_sks
    from (
        select
            *,
            max(longest_unbeaten) over (partition by league_code, season_api_year) as max_unbeaten,
            max(longest_winless) over (partition by league_code, season_api_year) as max_winless
        from team_longest
    )
    group by league_code, season_api_year
)

select
    t.league_code,
    t.season_api_year,
    t.competition_type,
    t.entity_type,
    t.matches_played,
    t.total_goals,
    t.drawn_matches,
    b.fixture_sk as biggest_margin_fixture_sk,
    b.home_team_sk as biggest_margin_home_team_sk,
    b.away_team_sk as biggest_margin_away_team_sk,
    b.goals_home as biggest_margin_goals_home,
    b.goals_away as biggest_margin_goals_away,
    b.round_name as biggest_margin_round_name,
    b.kickoff_datetime as biggest_margin_kickoff_datetime,
    g.fixture_sk as most_goals_fixture_sk,
    g.home_team_sk as most_goals_home_team_sk,
    g.away_team_sk as most_goals_away_team_sk,
    g.goals_home as most_goals_goals_home,
    g.goals_away as most_goals_goals_away,
    g.round_name as most_goals_round_name,
    g.kickoff_datetime as most_goals_kickoff_datetime,
    if(r.longest_unbeaten_run >= 2, r.longest_unbeaten_run, null) as longest_unbeaten_run,
    if(r.longest_unbeaten_run >= 2, r.longest_unbeaten_team_sks, []) as longest_unbeaten_team_sks,
    if(r.longest_winless_run >= 2, r.longest_winless_run, null) as longest_winless_run,
    if(r.longest_winless_run >= 2, r.longest_winless_team_sks, []) as longest_winless_team_sks,
    round(t.total_goals / t.matches_played, 2) as goals_per_match_played,
    if(t.entity_type = 'national', null, t.home_wins) as home_wins,
    if(t.entity_type = 'national', null, t.away_wins) as away_wins
from season_totals as t
left join biggest_margin as b
    on
        t.league_code = b.league_code
        and t.season_api_year = b.season_api_year
left join most_goals as g
    on
        t.league_code = g.league_code
        and t.season_api_year = g.season_api_year
left join league_runs as r
    on
        t.league_code = r.league_code
        and t.season_api_year = r.season_api_year
