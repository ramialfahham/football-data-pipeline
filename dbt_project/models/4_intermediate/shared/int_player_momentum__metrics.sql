{{ config(materialized='table') }}

{#
  W1 momentum builder — player.

  For each upcoming fixture side, aggregates raw player stat totals for every player who appeared
  in the side's window legs. The window selection is NOT re-derived here — it is consumed from the
  shared int_team_momentum_window model (extracted in #323), the SAME selection the team aggregate
  (int_team_momentum__metrics) and the drill-down list (mart_team_momentum_window) use. This keeps
  the player top-players strip and the team form panel on ONE window and prevents drift (#484).
  No ratios — those are computed in mart_player_momentum.

  Window (carried through from int_team_momentum_window):
  - window_type='last_5' (default): the team's last 5 finished matches, cross-competition within
    the same entity_type; season-capped for clubs, recency-only for national teams.
  - window_type='tournament_to_date' / 'qualifiers' (GAP-18, matrix §4): on a tournament fixture
    (world_championship / continental_championship) the window is the CUMULATIVE within-tournament
    (or qualifier) set, uncapped — so the player strip matches the team form on tournament fixtures.

  Grain: (upcoming_fixture_sk, team_sk, player_sk).

  Scope: all competition types — club and national. W1 is shown alongside W2 for every fixture;
  both numbers are always presented together.

  A player absent from some of the window legs contributes stats only for the matches they appeared
  in — honest absence, not zero. games_in_window is the player's appearance count within the side's
  window (0..5 for last_5, uncapped for tournament windows), not the team window size. It counts legs
  the player actually PLAYED (minutes > 0), so 0 is legitimate: named in the matchday squad for the
  window's legs but never brought on.

  passes_accurate_player is derived per fixture as ROUND(passes_player * passes_accuracy_percent / 100)
  then summed; inherits small rounding error.

  saves_player_pct requires goals_against_player which is not currently carried in int_legs__player_match —
  mart_player_momentum will emit null for that metric.
#}

with window_legs as (
    select
        upcoming_fixture_sk,
        team_sk,
        season_api_year,
        entity_type,
        window_type,
        leg_fixture_sk
    from {{ ref('int_team_momentum_window') }}
),

-- Aggregate player stats across the side's window legs
player_agg as (
    select
        wl.upcoming_fixture_sk,
        wl.team_sk,
        p.player_sk,
        wl.season_api_year,
        wl.entity_type,
        wl.window_type,
        -- pitch time required, same rule as the season models (CPO 2026-07-23): the provider lists
        -- whole matchday squads, so count(*) counted unused substitutes as appearances. 0 is now a
        -- legitimate value (named in the squad for window legs but never brought on).
        countif(coalesce(p.minutes_played, 0) > 0) as games_in_window,
        any_value(p.position_code) as position_code,
        sum(p.goals_total) as goals_total,
        sum(p.goals_against) as goals_against_player,
        sum(p.goals_assists) as goals_assists,
        sum(p.saves) as saves_player,
        sum(p.shots_total) as shots_player,
        sum(p.shots_on) as shots_on,
        sum(p.passes_total) as passes_player,
        sum(p.passes_key) as passes_key_player,
        sum(p.tackles_total) as tackles_player,
        sum(p.tackles_blocks) as blocks_player,
        sum(p.tackles_interceptions) as interceptions_player,
        sum(p.duels_total) as duels_player,
        sum(p.duels_won) as duels_won_player,
        sum(p.dribbles_attempts) as dribbles_attempts_player,
        sum(p.dribbles_success) as dribbles_success_player,
        sum(p.cards_yellow) as cards_yellow_player,
        sum(p.cards_red) as cards_red_player,
        sum(p.offsides) as offsides_player,
        sum(p.dribbles_past) as dribbles_past_player,
        sum(p.penalty_won) as penalty_won_player,
        sum(p.penalty_committed) as penalty_committed_player,
        -- passes_accurate_player: derived per fixture, then summed (small rounding error)
        sum(
            safe_cast(
                round(p.passes_total * p.passes_accuracy_percent / 100.0) as int64
            )
        ) as passes_accurate_player
    from window_legs as wl
    inner join {{ ref('int_legs__player_match') }} as p
        on
            wl.leg_fixture_sk = p.fixture_sk
            and wl.team_sk = p.team_sk
    group by
        wl.upcoming_fixture_sk,
        wl.team_sk,
        p.player_sk,
        wl.season_api_year,
        wl.entity_type,
        wl.window_type
)

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    season_api_year,
    entity_type,
    window_type,
    games_in_window,
    position_code,
    goals_total,
    goals_against_player,
    goals_assists,
    saves_player,
    shots_player,
    shots_on,
    passes_player,
    passes_key_player,
    passes_accurate_player,
    tackles_player,
    blocks_player,
    interceptions_player,
    duels_player,
    duels_won_player,
    dribbles_attempts_player,
    dribbles_success_player,
    cards_yellow_player,
    cards_red_player,
    offsides_player,
    dribbles_past_player,
    penalty_won_player,
    penalty_committed_player
from player_agg
