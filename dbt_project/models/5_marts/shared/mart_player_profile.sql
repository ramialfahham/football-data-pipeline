{{ config(materialized='table') }}

{#
  Player profile (#325). One row per (player, competition-season): the player's season profile a
  player page renders. Mirrors mart_team_profile.

  #480 consolidation: the per-season aggregation now COMPOSES the shared
  int_player_season__metrics (the single player-season rollup) instead of re-aggregating
  fct_fixture_player_stats inline. Identity (dim_player), the modal season position, and the GK
  full-triple (saves / shots_on_target_faced) are assembled here. Numbers are unchanged — the shared
  int reproduces the catalogue (ROUND-weighted) computations this mart used. Per-board leaderboard
  ranks moved to mart_leaderboards (the LONG single-surface; the 3 rank columns here were retired).

  Metric governance (catalogue-only v1): every metric is a metric_catalogue row computed by its
  catalogue formula — counts + the four catalogued player ratios. No invented or uncatalogued metrics
  (no goal_conversion, no player shot_accuracy). Per-90 metrics now exist in the catalogue for the
  player benchmark, but the profile does not carry them. Beyond the catalogue metrics, only raw
  descriptors are carried: appearances / starts / minutes, identity, modal position.

  Grain: (player_sk, season_sk). A player active in two competitions in one season has one row per
  competition-season. Only finished matches with a player-stats row contribute (honest absence).
#}

with season as (
    select * from {{ ref('int_player_season__metrics') }}
),

players as (
    select * from {{ ref('dim_player') }}
),

-- Most-frequent position that season (role badge); nulls excluded.
positions as (
    select
        s.player_sk,
        f.season_sk,
        s.position_code
    from {{ ref('fct_fixture_player_stats') }} as s
    inner join {{ ref('fct_fixture') }} as f
        on s.fixture_sk = f.fixture_sk
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and s.position_code is not null
),

modal_position as (
    select
        player_sk,
        season_sk,
        position_code
    from positions
    group by
        player_sk,
        season_sk,
        position_code
    qualify row_number() over (
        partition by player_sk, season_sk
        order by count(*) desc
    ) = 1
)

select
    {{ dbt_utils.generate_surrogate_key(['a.player_sk', 'a.season_sk']) }}
        as player_season_sk,
    a.player_sk,
    a.season_sk,
    a.league_sk,
    a.league_code,
    a.season_api_year,
    -- identity + descriptors (not catalogue metrics)
    p.player_name,
    p.player_first_name,
    p.player_last_name,
    p.player_nationality,
    p.player_birth_date,
    p.player_birth_place,
    p.player_birth_country,
    p.player_height,
    p.player_weight,
    p.player_position,
    p.player_photo_url,
    mp.position_code,
    a.appearances,
    a.starts,
    a.substitute_appearances,
    a.minutes,
    -- catalogue count metrics
    a.goals,
    a.assists,
    a.shots_on_target,
    a.passes_total,
    a.passes_key,
    a.passes_accurate,
    a.tackles_total,
    a.tackles_interceptions,
    a.tackles_blocks,
    a.duels_total,
    a.duels_won,
    a.dribbles_attempts,
    a.dribbles_success,
    a.dribbles_past,
    a.offsides,
    a.cards_yellow,
    a.cards_red,
    a.penalty_won,
    a.penalty_committed,
    -- GK atomics (GAP-12): the save full-triple — saves of shots faced
    a.goals_saves as saves,
    a.goals_saves + a.goals_conceded as shots_on_target_faced,
    -- catalogue ratio metrics (catalogue formula; null when denom 0)
    a.pass_accuracy_pct,
    a.duels_won_pct,
    a.dribbles_success_pct,
    a.save_pct
from season as a
left join players as p
    on a.player_sk = p.player_sk
left join modal_position as mp
    on
        a.player_sk = mp.player_sk
        and a.season_sk = mp.season_sk
