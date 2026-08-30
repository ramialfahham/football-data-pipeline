{{ config(materialized='view') }}

{#
  mart_leaderboards — LONG per-board player rankings (the Leaderboards block; content_architecture §3).
  Generalises the retired mart_top_scorers beyond goals. One row per (player, board): the player's rank on
  that board within its competition-season. Season-to-date, composed from the canonical
  int_player_season__metrics (the single source) + dim_player identity — NOT mart-from-mart.

  14 boards: 9 COUNT + 5 RATE (#506). metric_key = the catalogue metric_id. rank = DENSE_RANK over the
  board's metric desc within (league_code, season_api_year): ties share a rank, no ranks are skipped, and
  the top-10 cut is inclusive of ties (the mart_top_scorers convention). Only players with a positive
  value on a board are ranked (a leaderboard shows positive performers).

  RATE boards add a qualification rule (CPO, #506) so a tiny sample can't game a rate: minutes >= 270
  (3 full matches), a position scope, and — for finishing — a shots-on-target floor. pass / duels /
  dribble / finishing are outfield (excl. GK); save is GK-only. finishing also needs
  shots_on_goal_player >= 10 (minutes don't bound shot count, so a 1-shot 1-goal player would otherwise
  read a perfect rate). finishing_efficiency_player_pct is now open-play conversion in [0, 1] (CPO Option A).
  sort_value is FLOAT64: it holds both the integer counts and the 0-1 rates (the values are unchanged).

  Each row carries the union of the boards' display atoms so the export selects per board (marts contain
  what we show); sort_value is the board's own ranked value. Grain: (player_sk, season_sk, metric_key).
#}

{% set count_boards = [
    'goals',
    'scorer_points',
    'shots_on_goal_player',
    'dribbles_success',
    'passes_total',
    'passes_key',
    'duels_won',
    'defensive_actions',
    'cards_total',
] %}

{# RATE boards (#506): qualify on minutes >= 270 + a position scope (+ a SoT floor for finishing). #}
{% set outfield = "player_position is not null and player_position != 'Goalkeeper'" %}
{% set rate_boards = [
    {'key': 'pass_accuracy_pct', 'qualify': outfield},
    {'key': 'duels_won_pct', 'qualify': outfield},
    {'key': 'dribbles_success_pct', 'qualify': outfield},
    {'key': 'finishing_efficiency_player_pct', 'qualify': outfield ~ ' and shots_on_goal_player >= 10'},
    {'key': 'save_pct', 'qualify': "player_position = 'Goalkeeper'"},
] %}

{# Unified board specs — each carries its own WHERE so ONE ranked loop drives the union-all
   guard. Count boards rank all positive performers; rate boards add the qualification rule. #}
{% set boards = [] %}
{% for key in count_boards %}
{% do boards.append({'key': key, 'where': key ~ ' > 0'}) %}
{% endfor %}
{% for board in rate_boards %}
{% set rate_where = 'minutes >= 270 and ' ~ board.qualify ~ ' and ' ~ board.key ~ ' > 0' %}
{% do boards.append({'key': board.key, 'where': rate_where}) %}
{% endfor %}

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
        s.shots_on_goal_player,
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
        s.pass_accuracy_pct,
        s.duels_won_pct,
        s.dribbles_success_pct,
        s.save_pct,
        s.finishing_efficiency_player_pct,
        p.player_name,
        p.player_nationality,
        p.player_position,
        p.player_photo_url
    from season as s
    left join players as p on s.player_sk = p.player_sk
),

ranked as (
    {% for board in boards %}
    select
        base.*,
        '{{ board.key }}' as metric_key,
        cast({{ board.key }} as float64) as sort_value,
        dense_rank() over (
            partition by league_code, season_api_year
            order by {{ board.key }} desc
        ) as board_rank
    from base
    where {{ board.where }}
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
    shots_on_goal_player,
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
    cards_total,
    pass_accuracy_pct,
    duels_won_pct,
    dribbles_success_pct,
    save_pct,
    finishing_efficiency_player_pct
from ranked
where board_rank <= 10
