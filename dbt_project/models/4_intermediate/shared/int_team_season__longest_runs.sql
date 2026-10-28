{#
  Each team's longest unbeaten and longest winless run in a competition-season: the longest
  unbroken stretch of finished matches ordered by kickoff, not the run it is on now (the team
  profile's streaks carry that). Gaps and islands: a run's island id is the count of run-breaking
  results up to and including this match, so every match after a break starts a new island.
  longest_unbeaten / longest_winless hold the raw lengths, which the competition season summary
  reduces to the league's longest; longest_unbeaten_run / longest_winless_run apply the run rule
  the competition page shows, a run of one match is no run, so they are NULL below two.
  Grain: (league_code, season_api_year, team_sk).
#}

with legs as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        team_sk,
        kickoff_datetime,
        result
    from {{ ref('int_legs__team_match') }}
),

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
)

select
    league_code,
    season_api_year,
    team_sk,
    longest_unbeaten,
    longest_winless,
    if(longest_unbeaten >= 2, longest_unbeaten, null) as longest_unbeaten_run,
    if(longest_winless >= 2, longest_winless, null) as longest_winless_run
from team_longest
