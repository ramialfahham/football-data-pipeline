{{ config(materialized='table') }}

{#
  W1 momentum mart — player.

  Computes final displayed metrics from the raw sums in int_player_momentum__metrics.
  Raw counts (goals, assists, cards, …) are passed through directly. Ratios
  (save_pct, dribbles_success_pct, passes_accuracy_player_pct, duels_won_pct) are
  computed here via safe_divide — NULL when denominator is zero.

  window_type is carried through from the builder: last_5 for most fixtures, or the
  cumulative tournament_to_date / qualifiers window on tournament fixtures (GAP-18) —
  the same window the team form panel uses (#484).

  Grain: (upcoming_fixture_sk, team_sk, player_sk).

  save_pct is only meaningful for goalkeepers (position_code = 'G'); the column
  is present for all players but will be NULL for outfield players whose
  saves and goals_against are both zero/null.
#}

with builder as (
    select * from {{ ref('int_player_momentum__metrics') }}
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
    b.saves,
    b.shots_on,
    b.passes_key_player,
    b.passes_accurate_player,
    b.passes_player,
    b.tackles_player,
    b.blocks_player,
    b.interceptions_player,
    b.duels_won,
    b.duels_total,
    b.dribbles_success,
    b.dribbles_attempts,
    b.dribbles_past_player,
    b.offsides_player,
    b.penalty_won,
    b.penalty_committed_player,
    b.cards_yellow_player,
    b.cards_red_player,
    -- calculations
    b.team_sk = f.home_team_sk as is_home,
    -- ratios
    safe_divide(b.saves, b.saves + b.goals_against) as save_pct,
    safe_divide(b.dribbles_success, b.dribbles_attempts) as dribbles_success_pct,
    safe_divide(b.passes_accurate_player, b.passes_player) as passes_accuracy_player_pct,
    safe_divide(b.duels_won, b.duels_total) as duels_won_pct,
    -- per-side ranking for the top-players strip (GAP-19.2): goals, then assists, then
    -- key passes (the order named in the GAP); ROW_NUMBER = strict pick order, player_sk
    -- breaks ties deterministically. Selection rank, so ROW_NUMBER not DENSE_RANK.
    row_number() over (
        partition by b.upcoming_fixture_sk, b.team_sk
        order by
            coalesce(b.goals_total, 0) desc,
            coalesce(b.goals_assists, 0) desc,
            coalesce(b.passes_key_player, 0) desc,
            b.player_sk asc
    ) as top_player_rank
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
