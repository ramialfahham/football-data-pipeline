{{ config(materialized='table') }}

{#
  Trailing run lengths — team, per competition-season (#324, the lighter layer).

  For each (team, season) the length of the current unbroken run as of that
  season's most recent match: unbeaten / win / winless / clean-sheet / scoring.
  For the current season this is the live streak; for a finished season it is the
  end-of-season trailing run.

  A run length is the count of most-recent consecutive matches that satisfy the
  condition before the first match that breaks it (counting from the latest match
  backwards). If no match breaks it, the run spans the whole season.

  Grain: (team_sk, season_sk).
#}

with legs as (
    select
        team_sk,
        season_sk,
        league_code,
        season_api_year,
        fixture_sk,
        kickoff_datetime,
        result,
        goals_for,
        goals_against
    from {{ ref('int_legs__team_match') }}
),

ranked as (
    select
        team_sk,
        season_sk,
        league_code,
        season_api_year,
        result,
        goals_for,
        goals_against,
        row_number() over (
            partition by team_sk, season_sk
            order by kickoff_datetime desc, fixture_sk desc
        ) as recency_rank
    from legs
),

-- For each run type, find the recency_rank of the first match (from the latest
-- backwards) that BREAKS the run. The run length is that rank minus one, or the
-- whole season when nothing breaks it.
agg as (
    select
        team_sk,
        season_sk,
        any_value(league_code) as league_code,
        any_value(season_api_year) as season_api_year,
        count(*) as matches_in_season,
        min(if(result = 'L', recency_rank, null)) as first_loss_rank,
        min(if(result != 'W', recency_rank, null)) as first_nonwin_rank,
        min(if(result = 'W', recency_rank, null)) as first_win_rank,
        min(if(coalesce(goals_against, 0) > 0, recency_rank, null))
            as first_conceded_rank,
        min(if(coalesce(goals_for, 0) = 0, recency_rank, null))
            as first_blank_rank
    from ranked
    group by
        team_sk,
        season_sk
)

select
    team_sk,
    season_sk,
    league_code,
    season_api_year,
    matches_in_season,
    coalesce(first_loss_rank - 1, matches_in_season) as unbeaten_run,
    coalesce(first_nonwin_rank - 1, matches_in_season) as win_run,
    coalesce(first_win_rank - 1, matches_in_season) as winless_run,
    coalesce(first_conceded_rank - 1, matches_in_season) as clean_sheet_run,
    coalesce(first_blank_rank - 1, matches_in_season) as scoring_run
from agg
