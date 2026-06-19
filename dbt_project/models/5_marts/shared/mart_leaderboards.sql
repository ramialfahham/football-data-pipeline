{{ config(materialized='view') }}

{#
  mart_leaderboards — LONG per-board player rankings (the Leaderboards block; content_architecture §3).
  Generalises the retired mart_top_scorers beyond goals. One row per (player, board): the player's rank on
  that board within its competition-season. Season-to-date, composed from the canonical
  int_player_season__metrics (the single source) + dim_player identity — NOT mart-from-mart.

  9 COUNT boards (v1); metric_key = the catalogue metric_id. rank = DENSE_RANK over the board's metric
  desc within (league_code, season_api_year): ties share a rank, no ranks are skipped, and the top-10 cut
  is inclusive of ties (the mart_top_scorers convention). Only players with a positive value on a board
  are ranked (a leaderboard shows positive performers). The 5 RATE boards + their qualification floor are
  the deferred follow-up (#506).

  Each row carries the union of the boards' display atoms so the export selects per board (marts contain
  what we show); sort_value is the board's own ranked value. Grain: (player_sk, season_sk, metric_key).
#}

{% set boards = [
    'goals',
    'scorer_points',
    'shots_on_target',
    'dribbles_success',
    'passes_total',
    'passes_key',
    'duels_won',
    'defensive_actions',
    'cards_total',
] %}

with season as (
    select * from {{ ref('int_player_season__metrics') }}
),

players as (
    select
        player_sk,
        player_name,
        player_nationality,
        player_position,
        player_photo_url
    from {{ ref('dim_player') }}
),

base as (
    select
        s.player_sk,
        s.season_sk,
        s.league_sk,
        s.league_code,
        s.season_api_year,
        s.appearances,
        s.minutes,
        s.goals,
        s.assists,
        s.shots_on_target,
        s.dribbles_attempts,
        s.dribbles_success,
        s.passes_total,
        s.passes_key,
        s.duels_total,
        s.duels_won,
        s.tackles_total,
        s.tackles_interceptions,
        s.tackles_blocks,
        s.cards_yellow,
        s.cards_red,
        s.scorer_points,
        s.defensive_actions,
        s.cards_total,
        p.player_name,
        p.player_nationality,
        p.player_position,
        p.player_photo_url
    from season as s
    left join players as p on s.player_sk = p.player_sk
),

ranked as (
    {% for metric_key in boards %}
    select
        base.*,
        '{{ metric_key }}' as metric_key,
        {{ metric_key }} as sort_value,
        dense_rank() over (
            partition by league_code, season_api_year
            order by {{ metric_key }} desc
        ) as board_rank
    from base
    where {{ metric_key }} > 0
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
)

select
    {{ dbt_utils.generate_surrogate_key(['player_sk', 'season_sk', 'metric_key']) }}
        as player_leaderboard_sk,
    metric_key,
    board_rank as rank,
    sort_value,
    league_code,
    season_api_year,
    season_sk,
    league_sk,
    player_sk,
    player_name,
    player_nationality,
    player_position,
    player_photo_url,
    appearances,
    minutes,
    goals,
    assists,
    shots_on_target,
    dribbles_attempts,
    dribbles_success,
    passes_total,
    passes_key,
    duels_total,
    duels_won,
    tackles_total,
    tackles_interceptions,
    tackles_blocks,
    cards_yellow,
    cards_red,
    scorer_points,
    defensive_actions,
    cards_total
from ranked
where board_rank <= 10
