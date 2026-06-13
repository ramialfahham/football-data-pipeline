{{ config(materialized='table') }}

{#
  Player profile (#325). One row per (player, competition-season): the player's
  season profile a player page renders. Mirrors mart_team_profile.

  Metric governance (catalogue-only v1): every metric here is a row in the
  metric_catalogue seed (#327), computed by its catalogue formula — counts +
  the four catalogued player ratios. NO invented metrics (no per-90, no
  goal_conversion, no player shot_accuracy) — those are deferred to a catalogue
  extension approved by the CPO, driven by the new-UI design. Beyond the
  catalogue metrics, only raw descriptors are carried: appearances / starts /
  minutes, identity, and modal position. See feedback_metric_catalogue_governance.

  passes_accurate follows the catalogue definition exactly: per-fixture
  ROUND(passes_total × passes_accuracy_percent / 100) then summed (matches
  int_momentum__player / int_season_record__player; small rounding error).

  Grain: (player_sk, season_sk). A player active in two competitions in one
  season has one row per competition-season. Only finished matches with a
  player-stats row contribute (honest absence where statistics_players is off).
#}

with fixtures as (
    select
        fixture_sk,
        league_sk,
        season_sk,
        season_api_year
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

stats as (
    select * from {{ ref('fct_fixture_player_stats') }}
),

players as (
    select * from {{ ref('dim_player') }}
),

per_fixture as (
    select
        s.player_sk,
        f.league_sk,
        f.season_sk,
        s.league_code,
        f.season_api_year,
        s.position_code,
        s.minutes_played,
        s.is_starter,
        s.is_substitute,
        s.goals_total,
        s.goals_assists,
        s.goals_conceded,
        s.goals_saves,
        s.shots_on,
        s.passes_total,
        s.passes_key,
        s.passes_accuracy_percent,
        s.tackles_total,
        s.tackles_blocks,
        s.tackles_interceptions,
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
    from stats as s
    inner join fixtures as f
        on s.fixture_sk = f.fixture_sk
),

-- Most-frequent position that season (role badge); nulls excluded.
modal_position as (
    select
        player_sk,
        season_sk,
        position_code
    from per_fixture
    where position_code is not null
    group by
        player_sk,
        season_sk,
        position_code
    qualify row_number() over (
        partition by player_sk, season_sk
        order by count(*) desc
    ) = 1
),

agg as (
    select
        player_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        count(*) as appearances,
        countif(is_starter) as starts,
        countif(coalesce(is_substitute, false)) as substitute_appearances,
        sum(coalesce(minutes_played, 0)) as minutes,
        -- catalogue counts (window-agnostic metric_ids, computed over the season)
        sum(coalesce(goals_total, 0)) as goals,
        sum(coalesce(goals_assists, 0)) as assists,
        sum(coalesce(shots_on, 0)) as shots_on_target,
        sum(coalesce(passes_total, 0)) as passes_total,
        sum(coalesce(passes_key, 0)) as passes_key,
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
        -- passes_accurate: catalogue derivation (per-fixture round, then sum)
        sum(cast(round(passes_total * passes_accuracy_percent / 100.0) as int64))
            as passes_accurate,
        -- save_pct inputs; surfaced as saves / shots_on_target_faced (GAP-12)
        sum(coalesce(goals_saves, 0)) as goals_saves,
        sum(coalesce(goals_conceded, 0)) as goals_conceded
    from per_fixture
    group by
        player_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year
)

select
    {{ dbt_utils.generate_surrogate_key(['a.player_sk', 'a.season_sk']) }}
        as player_season_sk,
    a.player_sk,
    a.season_sk,
    a.league_sk,
    a.league_code,
    a.season_api_year,
    -- identity + descriptors (not catalogue metrics)
    p.player_name,
    p.player_first_name,
    p.player_last_name,
    p.player_nationality,
    p.player_birth_date,
    p.player_photo_url,
    mp.position_code,
    a.appearances,
    a.starts,
    a.substitute_appearances,
    a.minutes,
    -- catalogue count metrics
    a.goals,
    a.assists,
    a.shots_on_target,
    a.passes_total,
    a.passes_key,
    a.passes_accurate,
    a.tackles_total,
    a.tackles_interceptions,
    a.tackles_blocks,
    a.duels_total,
    a.duels_won,
    a.dribbles_attempts,
    a.dribbles_success,
    a.dribbles_past,
    a.offsides,
    a.cards_yellow,
    a.cards_red,
    a.penalty_won,
    a.penalty_committed,
    -- GK atomics (GAP-12): the save full-triple — saves of shots faced
    a.goals_saves as saves,
    -- catalogue ratio metrics (computed by catalogue formula; null when denom 0)
    a.goals_saves + a.goals_conceded as shots_on_target_faced,
    safe_divide(a.passes_accurate, a.passes_total) as pass_accuracy_pct,
    safe_divide(a.duels_won, a.duels_total) as duels_won_pct,
    safe_divide(a.dribbles_success, a.dribbles_attempts) as dribbles_success_pct,
    safe_divide(a.goals_saves, a.goals_saves + a.goals_conceded) as save_pct
from agg as a
left join players as p
    on a.player_sk = p.player_sk
left join modal_position as mp
    on
        a.player_sk = mp.player_sk
        and a.season_sk = mp.season_sk
