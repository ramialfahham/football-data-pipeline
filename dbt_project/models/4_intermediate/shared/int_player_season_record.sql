{{ config(materialized='table') }}

{#
  W2 season-record builder — player. Cumulative running totals over a player's finished
  matches within one competition+season, one row per match the player appeared in (totals
  THROUGH that match). The complement to int_player_momentum__metrics (W1 = last 5).

  Grain: (team_sk, player_sk, league_code, season_api_year, fixture_sk).

  A player-match leg exists wherever the API provides player stats, and the provider lists the whole
  matchday squad — so an UNUSED SUBSTITUTE arrives as a 0-minute leg. Those are filtered out below,
  because this model's row IS an appearance ("one row per match the player appeared in") and
  match_number/games_played must count matches actually played, not matchday selections. Before
  2026-07-23 they did not (CPO: "Then it is wrong"). Player ratios
  (save_pct, pass_accuracy_pct, duels_won_pct, dribbles_success_pct) are stat-over-stat
  from the same rows, so no coverage-restriction is needed (unlike the team builder's
  scoreline-vs-stat mix). Raw sums only — ratios live in the mart.

  Carries round_order + match_number for the deferred year-over-year surface.
  Season-bounded (partition by league_code, season_api_year). A national qualifying
  campaign is one season here — the provider stamps a whole campaign with a single
  season_api_year even though its matches span 2–3 calendar years — so this partition
  already cumulates the full campaign (§4 / #655).
#}

with player_legs as (
    select * from {{ ref('int_legs__player_match') }}
    -- pitch time required: an unused substitute is a matchday selection, not an appearance, and this
    -- model's grain is one row per APPEARANCE (see header). Same rule as the season/career models.
    where coalesce(minutes_played, 0) > 0
)

select
    team_sk,
    player_sk,
    league_code,
    season_api_year,
    fixture_sk,
    entity_type,
    kickoff_datetime,
    round_order,
    'season_to_date' as window_type,
    any_value(position_code) over w as position_code,
    row_number() over w_seq as match_number,
    row_number() over w_seq as games_played,
    sum(goals_total) over w as goals_total,
    sum(goals_against) over w as goals_against,
    sum(goals_assists) over w as goals_assists,
    sum(saves) over w as saves,
    sum(shots_total) over w as shots_total,
    sum(shots_on) over w as shots_on,
    sum(passes_total) over w as passes_total,
    sum(passes_key) over w as passes_key,
    sum(round(passes_total * passes_accuracy_percent / 100)) over w as passes_accurate,
    sum(tackles_total) over w as tackles_total,
    sum(tackles_blocks) over w as tackles_blocks,
    sum(tackles_interceptions) over w as tackles_interceptions,
    sum(duels_total) over w as duels_total,
    sum(duels_won) over w as duels_won,
    sum(dribbles_attempts) over w as dribbles_attempts,
    sum(dribbles_success) over w as dribbles_success,
    sum(dribbles_past) over w as dribbles_past,
    sum(offsides) over w as offsides,
    sum(penalty_won) over w as penalty_won,
    sum(penalty_committed) over w as penalty_committed,
    sum(cards_yellow) over w as cards_yellow,
    sum(cards_red) over w as cards_red
from player_legs
window
    w as (
        partition by team_sk, player_sk, league_code, season_api_year
        order by kickoff_datetime asc, fixture_sk asc
        rows between unbounded preceding and current row
    ),
    w_seq as (
        partition by team_sk, player_sk, league_code, season_api_year
        order by kickoff_datetime asc, fixture_sk asc
    )
