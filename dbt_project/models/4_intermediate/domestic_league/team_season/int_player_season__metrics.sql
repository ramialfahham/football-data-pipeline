{{ config(materialized='table') }}

{#
  Canonical per (player, competition-season) aggregate over all finished matches — the SINGLE player-season
  rollup consumed by mart_player_profile and mart_leaderboards (#480 consolidation; mart_player_season was
  retired with the leaderboards consolidation).

  #480 §8.3: this now COMPOSES int_player_club_season__metrics (the per-club atoms base) — it re-sums the
  club rows up to the competition-season and re-derives the ratios / per-90 / count composites from the
  re-summed atoms. Output columns and values are unchanged from the prior fct-direct aggregation: sum of
  per-club sums = the single sum, and the per-fixture ROUND-weighted passes_accurate is invariant to the
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
        sum(goals) as goals,
        sum(goals_penalty) as goals_penalty,
        sum(assists) as assists,
        sum(shots_total) as shots_total,
        sum(shots_on_goal) as shots_on_goal,
        sum(passes_total) as passes_total,
        sum(passes_key) as passes_key,
        sum(passes_accurate) as passes_accurate,
        sum(tackles_total) as tackles_total,
        sum(tackles_interceptions) as tackles_interceptions,
        sum(tackles_blocks) as tackles_blocks,
        sum(duels_total) as duels_total,
        sum(duels_won) as duels_won,
        sum(dribbles_attempts) as dribbles_attempts,
        sum(dribbles_success) as dribbles_success,
        sum(dribbles_past) as dribbles_past,
        sum(offsides) as offsides,
        sum(cards_yellow) as cards_yellow,
        sum(cards_red) as cards_red,
        sum(penalty_won) as penalty_won,
        sum(penalty_committed) as penalty_committed,
        sum(saves) as saves,
        sum(goals_against) as goals_against
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
    goals,
    goals_penalty,
    assists,
    shots_total,
    shots_on_goal,
    passes_total,
    passes_accurate,
    passes_key,
    tackles_total,
    tackles_interceptions,
    tackles_blocks,
    duels_total,
    duels_won,
    dribbles_attempts,
    dribbles_success,
    dribbles_past,
    offsides,
    cards_yellow,
    cards_red,
    penalty_won,
    penalty_committed,
    saves,
    goals_against,
    goals - goals_penalty as goals_open_play,
    -- count composites (leaderboard sort keys; sums of the atoms above) — metric_catalogue rows
    goals + assists as scorer_points,
    tackles_total + tackles_interceptions + tackles_blocks as defensive_actions,
    cards_yellow + cards_red as cards_total,
    safe_divide(passes_accurate, passes_total) as pass_accuracy_pct,
    safe_divide(duels_won, duels_total) as duels_won_pct,
    safe_divide(dribbles_success, dribbles_attempts) as dribbles_success_pct,
    safe_divide(saves, nullif(saves + goals_against, 0)) as save_pct,
    -- finishing efficiency (CPO Option A): open-play conversion = (goals − goals_penalty) /
    -- shots_on_goal. NULL ('—') when shots_on_goal is zero or the numerator falls outside
    -- [0, shots_on_goal] (rare broken-stat rows) — never >100%. (#506)
    case
        when (goals - goals_penalty) < 0 then null
        when (goals - goals_penalty) > shots_on_goal then null
        else safe_divide(goals - goals_penalty, shots_on_goal)
    end as finishing_efficiency,
    -- per-90 rates: count * 90 / minutes (minutes-normalised; null when minutes is zero).
    -- The comparison layer for the player competition benchmark; metric_catalogue rows.
    safe_divide(goals * 90, minutes) as goals_per90,
    safe_divide(assists * 90, minutes) as assists_per90,
    safe_divide((goals + assists) * 90, minutes) as scorer_points_per90,
    safe_divide(shots_on_goal * 90, minutes) as shots_on_goal_per90,
    safe_divide(passes_key * 90, minutes) as key_passes_per90,
    safe_divide(dribbles_success * 90, minutes) as dribbles_success_per90,
    safe_divide(passes_total * 90, minutes) as passes_per90,
    safe_divide(tackles_total * 90, minutes) as tackles_per90,
    safe_divide(tackles_interceptions * 90, minutes) as interceptions_per90,
    safe_divide(tackles_blocks * 90, minutes) as blocks_per90,
    safe_divide(
        (tackles_total + tackles_interceptions + tackles_blocks) * 90, minutes
    ) as defensive_actions_per90,
    safe_divide(duels_won * 90, minutes) as duels_won_per90,
    safe_divide(saves * 90, minutes) as saves_per90
from aggregated
