{{ config(materialized='table') }}

{#
  Games-played-aligned year-over-year — team, domestic leagues only (#324). Now covers ALL
  season metrics (not just the 3 totals): COMPOSES int_team_season__metrics_cumulative (the rate
  formulas applied at every matchday) at the cutoff N.

  For each domestic-league (team, current season), compares performance through the latest games
  played this season (N) against the SAME team's immediately prior season through its first N
  games. "This season vs last season, at the same point" — the only honest comparison while a
  season is running (a part-season vs a full season would mislead).

  Alignment is by GAMES PLAYED (match_number), not date and not the round-name number. For fixed-
  matchday leagues (one match per matchday) games-played == matchday. Games played is unambiguous
  in every format (parsed round numbers collide across multi-phase domestic formats).

  Metrics:
    - Totals (points / goals for / against): the cumulative scoreline sums (always present).
    - Rates (the LOCKED 16-row team display set): each is NULL on a side when that season's first
      N games are not fully stat-covered (the coverage gate carries over from the cumulative model)
      — an honest "no comparison", never a fabricated number.
    - delta = this − prev; NULL when either side is NULL (no prior season, or a coverage gap).

  Columns are grouped this-season / prev-season (simple selects) then the deltas (calculations),
  matching the model's prior shape (ST06). The rate formulas live once, in the cumulative model —
  here we only select + subtract. Scope: domestic_league only. Grain: (team_sk, league_code,
  season_api_year) — one row per team's CURRENT domestic season.
#}

with cml as (
    select * from {{ ref('int_team_season__metrics_cumulative') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

-- domestic-league cumulative rows only (YoY is meaningful for league formats; cups/tournaments
-- have no aligned comparison).
dom as (
    select c.*
    from cml as c
    inner join registry as r
        on c.league_code = r.league_code
    where r.competition_type = 'domestic_league'
),

-- current season per (team, league) and its latest games-played count N: the single most-recent
-- cumulative row (max season, then max match_number).
cur as (
    select * from dom
    qualify row_number() over (
        partition by team_sk, league_code
        order by season_api_year desc, match_number desc
    ) = 1
),

-- prior season through the same games-played cutoff (largest match_number <= N; a complete prior
-- season normally has >= N games).
prev as (
    select d.*
    from dom as d
    inner join cur as c
        on
            d.team_sk = c.team_sk
            and d.league_code = c.league_code
    where
        d.season_api_year = c.season_api_year - 1
        and d.match_number <= c.match_number
    qualify row_number() over (
        partition by d.team_sk, d.league_code
        order by d.match_number desc
    ) = 1
)

select
    cur.team_sk,
    cur.league_code,
    cur.season_api_year,
    cur.match_number as yoy_games_played_cutoff,
    prev.match_number as games_played_prev,
    -- this-season values (through N): 3 scoreline totals + the LOCKED 16-row rate metrics
    cur.points_won_sum_season as points_this_season,
    cur.goals_for_sum_season as goals_for_this_season,
    cur.goals_against_sum_season as goals_against_this_season,
    cur.goals_per_match as goals_per_match_this_season,
    cur.goals_against_per_match as goals_against_per_match_this_season,
    cur.clean_sheets_pct as clean_sheets_pct_this_season,
    cur.shots_per_match as shots_per_match_this_season,
    cur.danger_zone_ratio as danger_zone_ratio_this_season,
    cur.shots_on_goal_per_match as shots_on_goal_per_match_this_season,
    cur.finishing_efficiency as finishing_efficiency_this_season,
    cur.duels_per_match as duels_per_match_this_season,
    cur.duels_won_pct as duels_won_pct_this_season,
    cur.defensive_actions_per_match as defensive_actions_per_match_this_season,
    cur.passes_per_match as passes_per_match_this_season,
    cur.pass_accuracy as pass_accuracy_this_season,
    cur.key_passes_per_match as key_passes_per_match_this_season,
    cur.corner_kicks_per_match as corner_kicks_per_match_this_season,
    cur.corners_against_per_match as corners_against_per_match_this_season,
    cur.save_ratio as save_ratio_this_season,
    -- prior-season values (through the same N)
    prev.points_won_sum_season as points_prev_season,
    prev.goals_for_sum_season as goals_for_prev_season,
    prev.goals_against_sum_season as goals_against_prev_season,
    prev.goals_per_match as goals_per_match_prev_season,
    prev.goals_against_per_match as goals_against_per_match_prev_season,
    prev.clean_sheets_pct as clean_sheets_pct_prev_season,
    prev.shots_per_match as shots_per_match_prev_season,
    prev.danger_zone_ratio as danger_zone_ratio_prev_season,
    prev.shots_on_goal_per_match as shots_on_goal_per_match_prev_season,
    prev.finishing_efficiency as finishing_efficiency_prev_season,
    prev.duels_per_match as duels_per_match_prev_season,
    prev.duels_won_pct as duels_won_pct_prev_season,
    prev.defensive_actions_per_match as defensive_actions_per_match_prev_season,
    prev.passes_per_match as passes_per_match_prev_season,
    prev.pass_accuracy as pass_accuracy_prev_season,
    prev.key_passes_per_match as key_passes_per_match_prev_season,
    prev.corner_kicks_per_match as corner_kicks_per_match_prev_season,
    prev.corners_against_per_match as corners_against_per_match_prev_season,
    prev.save_ratio as save_ratio_prev_season,
    -- year-over-year deltas (this − prev; NULL when either side is NULL)
    cur.points_won_sum_season - prev.points_won_sum_season as points_delta_yoy,
    cur.goals_for_sum_season - prev.goals_for_sum_season as goals_for_delta_yoy,
    cur.goals_against_sum_season - prev.goals_against_sum_season as goals_against_delta_yoy,
    cur.goals_per_match - prev.goals_per_match as goals_per_match_delta_yoy,
    cur.goals_against_per_match - prev.goals_against_per_match as goals_against_per_match_delta_yoy,
    cur.clean_sheets_pct - prev.clean_sheets_pct as clean_sheets_pct_delta_yoy,
    cur.shots_per_match - prev.shots_per_match as shots_per_match_delta_yoy,
    cur.danger_zone_ratio - prev.danger_zone_ratio as danger_zone_ratio_delta_yoy,
    cur.shots_on_goal_per_match - prev.shots_on_goal_per_match as shots_on_goal_per_match_delta_yoy,
    cur.finishing_efficiency - prev.finishing_efficiency as finishing_efficiency_delta_yoy,
    cur.duels_per_match - prev.duels_per_match as duels_per_match_delta_yoy,
    cur.duels_won_pct - prev.duels_won_pct as duels_won_pct_delta_yoy,
    cur.defensive_actions_per_match - prev.defensive_actions_per_match as defensive_actions_per_match_delta_yoy,
    cur.passes_per_match - prev.passes_per_match as passes_per_match_delta_yoy,
    cur.pass_accuracy - prev.pass_accuracy as pass_accuracy_delta_yoy,
    cur.key_passes_per_match - prev.key_passes_per_match as key_passes_per_match_delta_yoy,
    cur.corner_kicks_per_match - prev.corner_kicks_per_match as corner_kicks_per_match_delta_yoy,
    cur.corners_against_per_match - prev.corners_against_per_match as corners_against_per_match_delta_yoy,
    cur.save_ratio - prev.save_ratio as save_ratio_delta_yoy
from cur
left join prev
    on
        cur.team_sk = prev.team_sk
        and cur.league_code = prev.league_code
