{{ config(materialized='table') }}

{#
  Games-played-aligned year-over-year — team, domestic leagues only (#324).

  For each domestic-league (team, current season), compares cumulative
  performance through the latest games played this season (N) against the SAME
  team's immediately prior season through its first N games. "This season vs
  last season, at the same point" — the only honest comparison while a season is
  running (a part-season vs a full season would mislead).

  Alignment is by GAMES PLAYED (match_number from int_team_season_record), not
  by date and not by the round-name number. For fixed-matchday European leagues
  (one match per matchday) games-played == matchday, which is the intended
  comparison. Parsed round numbers are NOT safe to align on: multi-phase domestic
  formats (e.g. Veikkausliiga regular + championship rounds) reuse the same
  trailing digit across phases, so a round_order cutoff double-counts. Games
  played is unambiguous in every format.

  Scope: competition_type = 'domestic_league' only. YoY is meaningful for league
  formats; cups/tournaments have no aligned comparison. Deltas are NULL where the
  prior season is not ingested (history_seasons = 1, or a promoted/relegated team
  with no prior top-flight season).

  Grain: (team_sk, league_code, season_api_year) — one row per team's CURRENT
  domestic season. season_sk is attached downstream in mart_team_profile.
#}

with std as (
    select
        team_sk,
        league_code,
        season_api_year,
        match_number,
        points_won,
        goals_for,
        goals_against
    from {{ ref('int_team_season_record') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

dom as (
    select s.*
    from std as s
    inner join registry as r
        on s.league_code = r.league_code
    where r.competition_type = 'domestic_league'
),

-- Current season per (team, league) and its latest games-played count N: the
-- single most-recent cumulative row (max season, then max match_number).
cur as (
    select
        team_sk,
        league_code,
        season_api_year as cur_season,
        match_number as games_played_cutoff,
        points_won as points_this_season,
        goals_for as goals_for_this_season,
        goals_against as goals_against_this_season
    from dom
    qualify row_number() over (
        partition by team_sk, league_code
        order by season_api_year desc, match_number desc
    ) = 1
),

-- Prior season cumulative through the same games-played cutoff (largest
-- match_number <= N; a complete prior season normally has >= N games).
prev as (
    select
        d.team_sk,
        d.league_code,
        d.match_number as games_played_prev,
        d.points_won as points_prev_season,
        d.goals_for as goals_for_prev_season,
        d.goals_against as goals_against_prev_season
    from dom as d
    inner join cur as c
        on
            d.team_sk = c.team_sk
            and d.league_code = c.league_code
    where
        d.season_api_year = c.cur_season - 1
        and d.match_number <= c.games_played_cutoff
    qualify row_number() over (
        partition by d.team_sk, d.league_code
        order by d.match_number desc
    ) = 1
)

select
    cur.team_sk,
    cur.league_code,
    cur.cur_season as season_api_year,
    cur.games_played_cutoff as yoy_games_played_cutoff,
    cur.points_this_season,
    cur.goals_for_this_season,
    cur.goals_against_this_season,
    prev.games_played_prev,
    prev.points_prev_season,
    prev.goals_for_prev_season,
    prev.goals_against_prev_season,
    cur.points_this_season - prev.points_prev_season as points_delta_yoy,
    cur.goals_for_this_season - prev.goals_for_prev_season as goals_for_delta_yoy,
    cur.goals_against_this_season - prev.goals_against_prev_season
        as goals_against_delta_yoy
from cur
left join prev
    on
        cur.team_sk = prev.team_sk
        and cur.league_code = prev.league_code
