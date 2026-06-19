{{ config(materialized='table') }}

{#
  Canonical per (player, competition-season) aggregate over all finished matches — the SINGLE
  player-season rollup consumed by BOTH mart_player_profile and mart_player_season (#480
  consolidation). Replaces the inline aggregation each mart previously duplicated.

  Grain: (player_sk, season_sk) — one row per player per competition-season (season_sk encodes the
  competition). league_sk / league_code / season_api_year carried for downstream slicing. (The
  per-club grain + this/last side-by-side are the deferred §8.3 follow-up; today's grain is kept.)

  Atoms follow docs/player_metrics_catalogue.md exactly:
  - passes_accurate = per-fixture ROUND(passes_total * passes_accuracy_percent / 100) then summed
    (catalogue-correct; the weighted-ratio numerator). Small per-fixture rounding error (~±1-2).
  - counts coalesce nulls to 0; appearances = count of finished player-stat rows (honest absence
    where statistics_players is off).
  - rates are NULL when the denominator is zero (never coerced to 0).
#}

with player_stats as (
    select * from {{ ref('fct_fixture_player_stats') }}
),

finished as (
    select
        fixture_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

per_fixture as (
    select
        s.player_sk,
        s.team_sk,
        f.league_sk,
        f.season_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        s.minutes_played,
        s.is_starter,
        s.is_substitute,
        s.goals_total,
        s.goals_assists,
        s.goals_saves,
        s.goals_conceded,
        s.shots_total,
        s.shots_on,
        s.passes_total,
        s.passes_key,
        s.passes_accuracy_percent,
        s.tackles_total,
        s.tackles_interceptions,
        s.tackles_blocks,
        s.duels_total,
        s.duels_won,
        s.dribbles_attempts,
        s.dribbles_success,
        s.dribbles_past,
        s.offsides,
        s.cards_yellow,
        s.cards_red,
        s.penalty_won,
        s.penalty_committed
    from player_stats as s
    inner join finished as f
        on s.fixture_sk = f.fixture_sk
),

aggregated as (
    select
        player_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        -- last known club in this competition-season (latest by kickoff)
        array_agg(team_sk ignore nulls order by kickoff_datetime desc limit 1)[
            safe_offset(0)
        ] as team_sk,
        count(*) as appearances,
        countif(is_starter) as starts,
        countif(coalesce(is_substitute, false)) as substitute_appearances,
        sum(coalesce(minutes_played, 0)) as minutes,
        sum(coalesce(goals_total, 0)) as goals,
        sum(coalesce(goals_assists, 0)) as assists,
        sum(coalesce(shots_total, 0)) as shots_total,
        sum(coalesce(shots_on, 0)) as shots_on_target,
        sum(coalesce(passes_total, 0)) as passes_total,
        sum(coalesce(passes_key, 0)) as passes_key,
        sum(
            cast(round(passes_total * passes_accuracy_percent / 100.0) as int64)
        ) as passes_accurate,
        sum(coalesce(tackles_total, 0)) as tackles_total,
        sum(coalesce(tackles_interceptions, 0)) as tackles_interceptions,
        sum(coalesce(tackles_blocks, 0)) as tackles_blocks,
        sum(coalesce(duels_total, 0)) as duels_total,
        sum(coalesce(duels_won, 0)) as duels_won,
        sum(coalesce(dribbles_attempts, 0)) as dribbles_attempts,
        sum(coalesce(dribbles_success, 0)) as dribbles_success,
        sum(coalesce(dribbles_past, 0)) as dribbles_past,
        sum(coalesce(offsides, 0)) as offsides,
        sum(coalesce(cards_yellow, 0)) as cards_yellow,
        sum(coalesce(cards_red, 0)) as cards_red,
        sum(coalesce(penalty_won, 0)) as penalty_won,
        sum(coalesce(penalty_committed, 0)) as penalty_committed,
        sum(coalesce(goals_saves, 0)) as goals_saves,
        sum(coalesce(goals_conceded, 0)) as goals_conceded
    from per_fixture
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
    assists,
    shots_total,
    shots_on_target,
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
    goals_saves,
    goals_conceded,
    -- count composites (leaderboard sort keys; sums of the atoms above) — metric_catalogue rows
    goals + assists as scorer_points,
    tackles_total + tackles_interceptions + tackles_blocks as defensive_actions,
    cards_yellow + cards_red as cards_total,
    safe_divide(passes_accurate, passes_total) as pass_accuracy_pct,
    safe_divide(duels_won, duels_total) as duels_won_pct,
    safe_divide(dribbles_success, dribbles_attempts) as dribbles_success_pct,
    safe_divide(goals_saves, nullif(goals_saves + goals_conceded, 0)) as save_pct
from aggregated
