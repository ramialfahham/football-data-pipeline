{{ config(materialized='table') }}

{#
  Per (player, competition-season, POSITION) aggregate over all finished matches — the position-split
  sibling of int_player_season__metrics, built for the player competition benchmark (content_architecture
  §6). Where int_player_season__metrics pools the whole season, this splits a player's legs by the position
  he played that match (fct_fixture_player_stats.position_code, recorded at match time) and aggregates each
  role separately. A player who logged minutes in two positions gets two rows, each carrying the per-90 he
  produced IN that role — so a multi-position player is benchmarked honestly per position, and the minutes
  >= 270 floor applied downstream both qualifies and assigns the position (CPO ruling 2026-06-23 B1/B2).

  position_code G/D/M/F -> position_group GK/DEF/MID/ATT; non-canonical codes ('-'/'SUB'/null, ~142 of
  1.67M legs) are dropped (they cannot be assigned a position). Atom formulas mirror int_player_season__
  metrics exactly, so a single-position player's per-90 here equals his whole-season per-90 there.

  Grain: (player_sk, season_sk, position_group). No floor here — the benchmark engine/mart filter
  minutes >= 270. The 18 benchmark metrics (per-90 + rates) are listed in the player_benchmark_metrics()
  macro (shared with int_competition_benchmarks__player + mart_competition_benchmarks__player).
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
        season_api_year
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

-- Penalty goals per (fixture, player) from match events, for the open-play finishing
-- numerator (CPO Option A). goals_total stays authoritative; only the penalty component is
-- event-derived. (Player goals_total already excludes own goals.)
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
        f.league_sk,
        f.season_sk,
        f.league_code,
        f.season_api_year,
        s.minutes_played,
        s.goals_total,
        s.goals_assists,
        s.saves,
        s.goals_against,
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
        coalesce(ev.penalty_goals, 0) as goals_penalty,
        case s.position_code
            when 'G' then 'GK'
            when 'D' then 'DEF'
            when 'M' then 'MID'
            when 'F' then 'ATT'
        end as position_group
    from player_stats as s
    inner join finished as f
        on s.fixture_sk = f.fixture_sk
    left join events as ev
        on s.fixture_sk = ev.fixture_sk and s.player_sk = ev.player_sk
    where s.position_code in ('G', 'D', 'M', 'F')
),

aggregated as (
    select
        player_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        position_group,
        count(*) as appearances,
        sum(coalesce(minutes_played, 0)) as minutes,
        sum(coalesce(goals_total, 0)) as goals,
        sum(goals_penalty) as goals_penalty,
        sum(coalesce(goals_assists, 0)) as assists,
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
        sum(coalesce(saves, 0)) as saves,
        sum(coalesce(goals_against, 0)) as goals_against
    from per_fixture
    group by
        player_sk, league_sk, season_sk, league_code, season_api_year, position_group
)

select
    player_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    position_group,
    appearances,
    minutes,
    goals,
    assists,
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
    saves,
    goals_against,
    -- count composites (sums of the atoms above) — metric_catalogue rows
    goals + assists as scorer_points,
    tackles_total + tackles_interceptions + tackles_blocks as defensive_actions,
    -- rates: NULL when the denominator is zero (never coerced to 0)
    safe_divide(passes_accurate, passes_total) as pass_accuracy_pct,
    safe_divide(duels_won, duels_total) as duels_won_pct,
    safe_divide(dribbles_success, dribbles_attempts) as dribbles_success_pct,
    safe_divide(saves, nullif(saves + goals_against, 0)) as save_pct,
    -- finishing efficiency (CPO Option A): open-play conversion = (goals − goals_penalty) /
    -- shots_on_goal. NULL when shots_on_goal is zero or the numerator falls outside
    -- [0, shots_on_goal] — never >100%.
    case
        when (goals - goals_penalty) < 0 then null
        when (goals - goals_penalty) > shots_on_goal then null
        else safe_divide(goals - goals_penalty, shots_on_goal)
    end as finishing_efficiency,
    -- per-90 rates IN POSITION: count * 90 / minutes (null when minutes is zero)
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
