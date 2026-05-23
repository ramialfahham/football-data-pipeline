{{ config(materialized='table') }}

{#
  Per (league_code, season_api_year, player_sk) aggregate statistics over all finished matches.
  Mirrors int_team_season__full_season_metrics at player grain.
  Grain: (league_code, season_api_year, player_sk).

  Used by:
    - int_matchday__fixture_player_insights (WC pre-tournament: full domestic season window)
    - Future player profile / season-recap surface

  Atom definitions follow docs/player_metrics_catalogue.md exactly.
  Rates are null when the denominator is zero; never coerced to 0.
#}

with import_fct_fixture_player_stats as (
    select * from {{ ref('fct_fixture_player_stats') }}
),

import_fct_fixture as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        status_short,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

player_finished_legs as (
    select
        fps.player_sk,
        fps.team_sk,
        fps.fixture_sk,
        fps.minutes_played,
        fps.goals_total,
        fps.goals_assists,
        fps.shots_on,
        fps.dribbles_success,
        fps.dribbles_attempts,
        fps.passes_total,
        fps.passes_accuracy_percent,
        fps.passes_key,
        fps.duels_total,
        fps.duels_won,
        fps.tackles_total,
        fps.tackles_interceptions,
        fps.tackles_blocks,
        fps.goals_saves,
        fps.goals_conceded,
        fps.cards_yellow,
        fps.cards_red,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime
    from import_fct_fixture_player_stats as fps
    inner join import_fct_fixture as f
        on fps.fixture_sk = f.fixture_sk
),

aggregated as (
    select
        league_code,
        season_api_year,
        player_sk,
        -- last known club team in this league/season for domestic-league resolution
        any_value(team_sk order by kickoff_datetime desc) as team_sk,
        count(distinct fixture_sk) as matches_played,
        sum(coalesce(minutes_played, 0)) as minutes_played_total,
        -- Leaderboard 1: scorer points
        sum(goals_total) as goals,
        sum(goals_assists) as assists,
        -- Leaderboard 2: shots on target
        sum(shots_on) as shots_on,
        -- Leaderboard 3: successful dribbles
        sum(dribbles_success) as dribbles_success,
        sum(dribbles_attempts) as dribbles_attempts,
        -- Leaderboard 4: key passes
        sum(passes_key) as passes_key,
        -- Leaderboard 5: pass accuracy
        sum(passes_total) as passes_total,
        -- Accurate passes derived: floor(passes_total * accuracy_pct / 100) per fixture, then sum
        sum(
            safe_cast(
                floor(coalesce(passes_total, 0) * coalesce(passes_accuracy_percent, 0) / 100.0)
                as int64
            )
        ) as passes_accurate,
        -- Leaderboard 6: duels won
        sum(duels_total) as duels_total,
        sum(duels_won) as duels_won,
        -- Leaderboard 7: defensive actions
        sum(tackles_total) as tackles_total,
        sum(tackles_interceptions) as interceptions,
        sum(tackles_blocks) as blocks,
        -- Leaderboard 8: save percentage
        sum(goals_saves) as goals_saves,
        sum(goals_conceded) as goals_conceded,
        -- Leaderboard 9: cards
        sum(cards_yellow) as cards_yellow,
        sum(cards_red) as cards_red
    from player_finished_legs
    group by league_code, season_api_year, player_sk
)

select
    league_code,
    season_api_year,
    player_sk,
    team_sk,
    matches_played,
    minutes_played_total,
    -- Raw counts
    goals,
    assists,
    shots_on,
    dribbles_success,
    dribbles_attempts,
    passes_key,
    passes_total,
    passes_accurate,
    duels_total,
    duels_won,
    tackles_total,
    interceptions,
    blocks,
    goals_saves,
    goals_conceded,
    cards_yellow,
    cards_red,
    -- Derived rates (null when denominator zero)
    safe_divide(dribbles_success, dribbles_attempts) as dribbles_success_pct,
    safe_divide(passes_accurate, passes_total) as pass_accuracy_pct,
    safe_divide(duels_won, duels_total) as duels_won_pct,
    safe_divide(goals_saves, nullif(goals_saves + goals_conceded, 0)) as save_pct
from aggregated
