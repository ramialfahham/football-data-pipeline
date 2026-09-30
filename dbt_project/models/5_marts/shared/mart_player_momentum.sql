{#
  W1 momentum mart — player.

  The displayed metrics of int_player_momentum__metrics, which computes every one of them (counts and
  ratios) from its catalogue formula. Goals, assists and shots on target are handed to the export under
  the keys the site reads (goals_total, goals_assists, shots_on).

  window_type is carried through from the builder: last_5 for most fixtures, or the
  cumulative tournament_to_date / qualifiers window on tournament fixtures (GAP-18) —
  the same window the team form panel uses (#484).

  Grain: (upcoming_fixture_sk, team_sk, player_sk).

  saves_player_pct is only meaningful for goalkeepers (position_code = 'G'); the column
  is present for all players but will be NULL for outfield players whose
  saves_player and goals_against_player are both zero/null.
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
    -- counts
    b.goals_player as goals_total,
    b.assists_player as goals_assists,
    b.saves_player,
    b.shots_on_goal_player as shots_on,
    b.passes_key_player,
    b.passes_accurate_player,
    b.passes_player,
    b.tackles_player,
    b.blocks_player,
    b.interceptions_player,
    b.duels_won_player,
    b.duels_player,
    b.dribbles_success_player,
    b.dribbles_attempts_player,
    b.dribbles_past_player,
    b.offsides_player,
    b.penalty_won_player,
    b.penalty_committed_player,
    b.cards_yellow_player,
    b.cards_red_player,
    -- ratios
    b.saves_player_pct,
    b.dribbles_success_player_pct,
    b.passes_accuracy_player_pct,
    b.duels_won_player_pct,
    -- calculations
    b.team_sk = f.home_team_sk as is_home,
    -- per-side ranking for the top-players strip (GAP-19.2): goals, then assists, then
    -- key passes (the order named in the GAP); ROW_NUMBER = strict pick order, player_sk
    -- breaks ties deterministically. Selection rank, so ROW_NUMBER not DENSE_RANK.
    row_number() over (
        partition by b.upcoming_fixture_sk, b.team_sk
        order by
            coalesce(b.goals_player, 0) desc,
            coalesce(b.assists_player, 0) desc,
            coalesce(b.passes_key_player, 0) desc,
            b.player_sk asc
    ) as top_player_rank
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
