{{ config(materialized='table') }}

{#
  W1 last-5 momentum mart — player.

  Computes final displayed metrics from the raw sums in int_momentum__player.
  Raw counts (goals, assists, cards, …) are passed through directly. Ratios
  (save_pct, dribbles_success_pct, pass_accuracy_pct, duels_won_pct) are
  computed here via safe_divide — NULL when denominator is zero.

  Grain: (upcoming_fixture_sk, team_sk, player_sk).

  save_pct is only meaningful for goalkeepers (position_code = 'G'); the column
  is present for all players but will be NULL for outfield players whose
  goals_saves and goals_conceded are both zero/null.
#}

with builder as (
    select * from {{ ref('int_momentum__player') }}
),

fixtures as (
    select
        fixture_sk,
        league_code,
        home_team_sk
    from {{ ref('fct_fixture') }}
)

select
    b.upcoming_fixture_sk,
    b.team_sk,
    b.player_sk,
    f.league_code,
    b.entity_type,
    b.season_api_year,
    b.window_type,
    b.games_in_window,
    b.position_code,
    -- raw counts
    b.goals_total,
    b.goals_assists,
    b.goals_saves,
    b.shots_on,
    b.passes_key,
    b.passes_accurate,
    b.passes_total,
    b.tackles_total,
    b.tackles_blocks,
    b.tackles_interceptions,
    b.duels_won,
    b.duels_total,
    b.dribbles_success,
    b.dribbles_attempts,
    b.dribbles_past,
    b.offsides,
    b.penalty_won,
    b.penalty_committed,
    b.cards_yellow,
    b.cards_red,
    -- calculations
    b.team_sk = f.home_team_sk as is_home,
    -- ratios
    safe_divide(b.goals_saves, b.goals_saves + b.goals_conceded) as save_pct,
    safe_divide(b.dribbles_success, b.dribbles_attempts) as dribbles_success_pct,
    safe_divide(b.passes_accurate, b.passes_total) as pass_accuracy_pct,
    safe_divide(b.duels_won, b.duels_total) as duels_won_pct,
    -- per-side ranking for the top-players strip (GAP-19.2): goals, then assists, then
    -- key passes (the order named in the GAP); ROW_NUMBER = strict pick order, player_sk
    -- breaks ties deterministically. Selection rank, so ROW_NUMBER not DENSE_RANK.
    row_number() over (
        partition by b.upcoming_fixture_sk, b.team_sk
        order by
            coalesce(b.goals_total, 0) desc,
            coalesce(b.goals_assists, 0) desc,
            coalesce(b.passes_key, 0) desc,
            b.player_sk asc
    ) as top_player_rank
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
