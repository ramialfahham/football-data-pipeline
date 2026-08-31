{{ config(materialized='table') }}

{#
  Canonical per (player, competition-season) aggregate over all finished matches — the SINGLE player-season
  rollup consumed by mart_player_profile and mart_leaderboards (#480 consolidation; mart_player_season was
  retired with the leaderboards consolidation).

  #480 §8.3: this now COMPOSES int_player_club_season__metrics (the per-club atoms base) — it re-sums the
  club rows up to the competition-season and re-derives the ratios / per-90 / count composites from the
  re-summed atoms. Output columns and values are unchanged from the prior fct-direct aggregation: sum of
  per-club sums = the single sum, and the per-fixture ROUND-weighted passes_accurate_player is invariant to the
  grouping level. team_sk = the player's last known club that competition-season, reproduced from the
  base's per-club last_kickoff_at.

  Grain: (player_sk, season_sk) — one row per player per competition-season (season_sk encodes the
  competition). Atoms follow the metric_catalogue.csv seed; counts coalesce nulls to 0; rates are NULL
  when the denominator is zero (never coerced to 0).
#}

with club_season as (
    select * from {{ ref('int_player_club_season__metrics') }}
),

aggregated as (
    select
        player_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        -- last known club this competition-season: the club whose latest kickoff is the latest overall
        -- (= the team of the player's last finished match — reproduces the prior fct-direct stamp). A
        -- player cannot appear for two clubs at the same instant, so last_kickoff_at is unique per club
        -- and no tie can occur; team_sk is a deterministic secondary sort purely for reproducibility.
        array_agg(team_sk ignore nulls order by last_kickoff_at desc, team_sk desc limit 1)[
            safe_offset(0)
        ] as team_sk,
        sum(appearances) as appearances,
        sum(starts) as starts,
        sum(substitute_appearances) as substitute_appearances,
        sum(minutes) as minutes,
        sum(goals_player) as goals_player,
        sum(goals_penalty_player) as goals_penalty_player,
        sum(assists_player) as assists_player,
        sum(shots_player) as shots_player,
        sum(shots_on_goal_player) as shots_on_goal_player,
        sum(passes_player) as passes_player,
        sum(passes_key_player) as passes_key_player,
        sum(passes_accurate_player) as passes_accurate_player,
        sum(tackles_player) as tackles_player,
        sum(interceptions_player) as interceptions_player,
        sum(blocks_player) as blocks_player,
        sum(duels_player) as duels_player,
        sum(duels_won_player) as duels_won_player,
        sum(dribbles_attempts_player) as dribbles_attempts_player,
        sum(dribbles_success_player) as dribbles_success_player,
        sum(dribbles_past_player) as dribbles_past_player,
        sum(offsides_player) as offsides_player,
        sum(cards_yellow_player) as cards_yellow_player,
        sum(cards_red_player) as cards_red_player,
        sum(penalty_won_player) as penalty_won_player,
        sum(penalty_committed_player) as penalty_committed_player,
        sum(saves_player) as saves_player,
        sum(goals_against_player) as goals_against_player
    from club_season
    group by player_sk, league_sk, season_sk, league_code, season_api_year
)

select
    player_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    appearances,
    starts,
    substitute_appearances,
    minutes,
    goals_player,
    goals_penalty_player,
    assists_player,
    shots_player,
    shots_on_goal_player,
    passes_player,
    passes_accurate_player,
    passes_key_player,
    tackles_player,
    interceptions_player,
    blocks_player,
    duels_player,
    duels_won_player,
    dribbles_attempts_player,
    dribbles_success_player,
    dribbles_past_player,
    offsides_player,
    cards_yellow_player,
    cards_red_player,
    penalty_won_player,
    penalty_committed_player,
    saves_player,
    goals_against_player,
    goals_player - goals_penalty_player as goals_open_play_player,
    -- count composites (leaderboard sort keys; sums of the atoms above) — metric_catalogue rows
    goals_player + assists_player as scorer_points_player,
    tackles_player + interceptions_player + blocks_player as defensive_actions_player,
    cards_yellow_player + cards_red_player as cards_player,
    safe_divide(passes_accurate_player, passes_player) as passes_accuracy_player_pct,
    safe_divide(duels_won_player, duels_player) as duels_won_player_pct,
    safe_divide(dribbles_success_player, dribbles_attempts_player) as dribbles_success_player_pct,
    safe_divide(saves_player, nullif(saves_player + goals_against_player, 0)) as saves_player_pct,
    -- finishing efficiency (CPO Option A): open-play conversion = (goals_player − goals_penalty_player) /
    -- shots_on_goal_player. NULL ('—') when shots_on_goal_player is zero or the numerator falls outside
    -- [0, shots_on_goal_player] (rare broken-stat rows) — never >100%. (#506)
    case
        when (goals_player - goals_penalty_player) < 0 then null
        when (goals_player - goals_penalty_player) > shots_on_goal_player then null
        else safe_divide(goals_player - goals_penalty_player, shots_on_goal_player)
    end as finishing_efficiency_player_pct,
    -- per-90 rates: count * 90 / minutes (minutes-normalised; null when minutes is zero).
    -- The comparison layer for the player competition benchmark; metric_catalogue rows.
    safe_divide(goals_player * 90, minutes) as goals_per90,
    safe_divide(assists_player * 90, minutes) as assists_per90,
    safe_divide((goals_player + assists_player) * 90, minutes) as scorer_points_per90,
    safe_divide(shots_on_goal_player * 90, minutes) as shots_on_goal_per90,
    safe_divide(passes_key_player * 90, minutes) as passes_key_per90,
    safe_divide(dribbles_success_player * 90, minutes) as dribbles_success_per90,
    safe_divide(passes_player * 90, minutes) as passes_per90,
    safe_divide(tackles_player * 90, minutes) as tackles_per90,
    safe_divide(interceptions_player * 90, minutes) as interceptions_per90,
    safe_divide(blocks_player * 90, minutes) as blocks_per90,
    safe_divide(
        (tackles_player + interceptions_player + blocks_player) * 90, minutes
    ) as defensive_actions_per90,
    safe_divide(duels_won_player * 90, minutes) as duels_won_per90,
    safe_divide(saves_player * 90, minutes) as saves_per90
from aggregated
