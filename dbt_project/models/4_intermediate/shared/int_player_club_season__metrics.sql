{{ config(materialized='table') }}

{#
  Canonical per (player, CLUB, competition-season) aggregate over all finished matches — the finest-grain
  player rollup (#480 §8.3). Where int_player_season__metrics pools a whole competition-season, this keeps
  the club axis: a player with a mid-season transfer gets one honest row per club (not the last-club
  collapse). It is the SINGLE atoms source both int_player_season__metrics (re-aggregated up to the
  competition-season) and mart_player_career (the per-club career log) COMPOSE — no divergent rollups.

  Grain: (player_sk, team_sk, season_sk) — season_sk encodes the competition, so this row is one player,
  at one club, in one competition-season. league_sk / league_code / season_api_year are carried for
  downstream slicing (each is functionally determined by season_sk).

  Atoms only — the summable COUNT measures, computed exactly as int_player_season__metrics does today
  (same coalesce-to-0, same per-fixture ROUND-weighted passes_accurate numerator). Ratios / per-90 / count
  composites are NOT here: they are non-summable, so they are derived where consumed (the competition-season
  rollup and any future per-club consumer), per the COMPOSE pattern. last_kickoff_at carries the club's
  latest kickoff so the rollup can reproduce the "last club that season" stamp.
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

-- Penalty goals per (fixture, player) from match events, for the open-play finishing numerator
-- (CPO Option A). event_detail='Penalty' = a scored penalty by this player; goals_total stays the
-- authoritative player goal count (already excludes own goals) — only the penalty component is
-- event-derived. Mirrors int_player_season__metrics exactly.
events as (
    select
        fixture_sk,
        player_sk,
        countif(event_type = 'Goal' and event_detail = 'Penalty') as penalty_goals
    from {{ ref('fct_fixture_event') }}
    where player_sk is not null
    group by fixture_sk, player_sk
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
        s.saves,
        s.goals_against,
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
        s.penalty_committed,
        coalesce(ev.penalty_goals, 0) as goals_penalty
    from player_stats as s
    inner join finished as f
        on s.fixture_sk = f.fixture_sk
    left join events as ev
        on s.fixture_sk = ev.fixture_sk and s.player_sk = ev.player_sk
),

aggregated as (
    select
        player_sk,
        team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        -- the club's latest kickoff this competition-season — lets the rollup pick the last club.
        max(kickoff_datetime) as last_kickoff_at,
        count(*) as appearances,
        countif(is_starter) as starts,
        countif(coalesce(is_substitute, false)) as substitute_appearances,
        sum(coalesce(minutes_played, 0)) as minutes,
        sum(coalesce(goals_total, 0)) as goals,
        sum(goals_penalty) as goals_penalty,
        sum(coalesce(goals_assists, 0)) as assists,
        sum(coalesce(shots_total, 0)) as shots_total,
        sum(coalesce(shots_on, 0)) as shots_on_goal,
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
        sum(coalesce(saves, 0)) as saves,
        sum(coalesce(goals_against, 0)) as goals_against
    from per_fixture
    group by player_sk, team_sk, league_sk, season_sk, league_code, season_api_year
)

select
    {{ dbt_utils.generate_surrogate_key(['player_sk', 'team_sk', 'season_sk']) }}
        as player_club_season_sk,
    player_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    last_kickoff_at,
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
    passes_key,
    passes_accurate,
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
    goals_against
from aggregated
