{{ config(materialized='table') }}

{#
  Appearances-aligned year-over-year — player, domestic leagues only (Phase C, #391;
  the player mirror of int_team_profile__yoy, #324).

  For each domestic-league (player, club, current season), compares cumulative output
  through the latest appearances this season (N) against the SAME player's immediately
  prior season AT THE SAME CLUB through its first N appearances. "This season vs last
  season, at the same point of the campaign" — the only honest comparison while a
  season is running (a part-season vs a full season would mislead).

  Alignment is by APPEARANCES (match_number from int_player_season_record — the running
  count of the player's finished appearances-with-stats), the player analog of the team
  builder's games played. Not by date, not by round number.

  Metric set (CPO 2026-07-03, the broader per-position set): goals, assists, shots on
  target, key passes, defensive actions (tackles + interceptions + blocks). Raw
  cumulative counts (per-90 / ratios live elsewhere); the delta is this - prev.

  Scope: competition_type = 'domestic_league' only — YoY is meaningful for league
  formats; cups/tournaments have no aligned comparison. Deltas are NULL where the prior
  season AT THIS CLUB is absent (a transfer, a first top-flight season, or
  history_seasons = 1).

  Grain: (team_sk, player_sk, league_code, season_api_year) — one row per player's
  CURRENT club-league season. season_sk is attached downstream in mart_player_profile
  via the player's primary club; a within-season same-league two-club spell surfaces
  the primary club there (an honest limit, rare).
#}

with std as (
    select
        team_sk,
        player_sk,
        league_code,
        season_api_year,
        match_number,
        goals_total,
        goals_assists,
        shots_on,
        passes_key,
        tackles_total + tackles_interceptions + tackles_blocks as defensive_actions
    from {{ ref('int_player_season_record') }}
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

-- Current season per (player, club, league) and its latest appearance count N: the
-- single most-recent cumulative row (max season, then max match_number).
cur as (
    select
        team_sk,
        player_sk,
        league_code,
        season_api_year as cur_season,
        match_number as appearances_cutoff,
        goals_total as goals_this_season,
        goals_assists as assists_this_season,
        shots_on as shots_on_goal_this_season,
        passes_key as key_passes_this_season,
        defensive_actions as defensive_actions_this_season
    from dom
    qualify row_number() over (
        partition by team_sk, player_sk, league_code
        order by season_api_year desc, match_number desc
    ) = 1
),

-- Prior season at the same club, cumulative through the same appearance cutoff
-- (largest match_number <= N; a complete prior season normally has >= N appearances).
prev as (
    select
        d.team_sk,
        d.player_sk,
        d.league_code,
        d.match_number as appearances_prev,
        d.goals_total as goals_prev_season,
        d.goals_assists as assists_prev_season,
        d.shots_on as shots_on_goal_prev_season,
        d.passes_key as key_passes_prev_season,
        d.defensive_actions as defensive_actions_prev_season
    from dom as d
    inner join cur as c
        on
            d.team_sk = c.team_sk
            and d.player_sk = c.player_sk
            and d.league_code = c.league_code
    where
        d.season_api_year = c.cur_season - 1
        and d.match_number <= c.appearances_cutoff
    qualify row_number() over (
        partition by d.team_sk, d.player_sk, d.league_code
        order by d.match_number desc
    ) = 1
)

select
    cur.team_sk,
    cur.player_sk,
    cur.league_code,
    cur.cur_season as season_api_year,
    cur.appearances_cutoff as yoy_appearances_cutoff,
    cur.goals_this_season,
    cur.assists_this_season,
    cur.shots_on_goal_this_season,
    cur.key_passes_this_season,
    cur.defensive_actions_this_season,
    prev.appearances_prev,
    prev.goals_prev_season,
    prev.assists_prev_season,
    prev.shots_on_goal_prev_season,
    prev.key_passes_prev_season,
    prev.defensive_actions_prev_season,
    cur.goals_this_season - prev.goals_prev_season as goals_delta_yoy,
    cur.assists_this_season - prev.assists_prev_season as assists_delta_yoy,
    cur.shots_on_goal_this_season - prev.shots_on_goal_prev_season
        as shots_on_goal_delta_yoy,
    cur.key_passes_this_season - prev.key_passes_prev_season as key_passes_delta_yoy,
    cur.defensive_actions_this_season - prev.defensive_actions_prev_season
        as defensive_actions_delta_yoy
from cur
left join prev
    on
        cur.team_sk = prev.team_sk
        and cur.player_sk = prev.player_sk
        and cur.league_code = prev.league_code
