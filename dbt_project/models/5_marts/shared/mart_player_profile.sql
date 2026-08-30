{{ config(materialized='table') }}

{#
  Player profile (#325). One row per (player, competition-season): the player's season profile a
  player page renders. Mirrors mart_team_profile.

  #480 consolidation: the per-season aggregation now COMPOSES the shared
  int_player_season__metrics (the single player-season rollup) instead of re-aggregating
  fct_fixture_player_stats inline. Identity (dim_player), the modal season position, and the GK
  full-triple (saves / shots_on_goal_against) are assembled here. Numbers are unchanged — the shared
  int reproduces the catalogue (ROUND-weighted) computations this mart used. Per-board leaderboard
  ranks moved to mart_leaderboards (the LONG single-surface; the 3 rank columns here were retired).

  Metric governance (catalogue-only v1): every metric is a metric_catalogue row computed by its
  catalogue formula — counts + the four catalogued player ratios. No invented or uncatalogued metrics
  (no goal_conversion, no player shot_accuracy). Per-90 metrics now exist in the catalogue for the
  player benchmark, but the profile does not carry them. Beyond the catalogue metrics, only raw
  descriptors are carried: appearances / starts / minutes, identity, modal position.

  Grain: (player_sk, season_sk). A player active in two competitions in one season has one row per
  competition-season. Only finished matches with a player-stats row contribute (honest absence).
#}

with season as (
    select * from {{ ref('int_player_season__metrics') }}
),

players as (
    select * from {{ ref('dim_player') }}
),

-- Most-frequent position that season (role badge); nulls excluded.
positions as (
    select
        s.player_sk,
        f.season_sk,
        s.position_code
    from {{ ref('fct_fixture_player_stats') }} as s
    inner join {{ ref('fct_fixture') }} as f
        on s.fixture_sk = f.fixture_sk
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and s.position_code is not null
),

modal_position as (
    select
        player_sk,
        season_sk,
        position_code
    from positions
    group by
        player_sk,
        season_sk,
        position_code
    qualify row_number() over (
        partition by player_sk, season_sk
        order by count(*) desc
    ) = 1
),

-- GAP-16: the player's team per competition-season (most-recent-match club + the current-club flag),
-- derived in dbt. The export selects by is_current_team — it never re-ranks (consumption-layer).
team_affiliation as (
    select * from {{ ref('int_player_season__team') }}
),

-- dim_team identity for the affiliated club (mirrors the dim_player identity join below).
teams as (
    select
        team_sk,
        team_name,
        team_logo_url,
        team_country
    from {{ ref('dim_team') }}
),

-- Phase C: appearances-aligned year-over-year for the player's PRIMARY club that
-- competition-season (mirrors int_team_profile__yoy -> mart_team_profile). Only the
-- latest season per (player, club, league) has a YoY row; older seasons get NULL.
yoy as (
    select * from {{ ref('int_player_profile__yoy') }}
),

-- Phase D bonus: goal-involvement share of the club's whole-season goals, for the player's PRIMARY club
-- that competition-season (content_architecture §6.4).
contribution as (
    select * from {{ ref('int_player_profile__contribution') }}
),

-- #846: the competition's type, and whether it is club or national football. Same two-step seed
-- join mart_player_career already uses. Needed because the season a player's page opens on is a
-- CLUB season (#848 made Overview, Performance and Career club-only), and a player-season row on
-- its own cannot tell club football from national.
registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

types as (
    select
        competition_type,
        entity_type
    from {{ ref('competition_types') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['a.player_sk', 'a.season_sk']) }}
        as player_season_sk,
    a.player_sk,
    a.season_sk,
    a.league_sk,
    a.league_code,
    a.season_api_year,
    reg.competition_type,
    ct.entity_type,
    -- identity + descriptors (not catalogue metrics)
    p.player_name,
    p.player_first_name,
    p.player_last_name,
    p.player_nationality,
    p.player_birth_date,
    p.player_birth_place,
    p.player_birth_country,
    p.player_height,
    p.player_weight,
    p.player_position,
    p.player_photo_url,
    mp.position_code,
    -- team affiliation (GAP-16): the most-recent-match club this competition-season + the current-club
    -- flag (the player's single most-recent finished match overall); identity from dim_team.
    ta.team_sk,
    coalesce(ta.is_current_team, false) as is_current_team,
    t.team_name,
    t.team_logo_url,
    t.team_country,
    a.appearances,
    a.starts,
    a.substitute_appearances,
    a.minutes,
    -- catalogue count metrics
    a.goals,
    a.assists,
    a.shots_on_goal_player,
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
    a.offsides_player,
    a.cards_yellow_player,
    a.cards_red_player,
    a.penalty_won,
    a.penalty_committed_player,
    -- GK atomics (GAP-12): the save full-triple — saves of shots faced
    a.saves,
    a.saves + a.goals_against as shots_on_goal_against,
    -- catalogue ratio metrics (catalogue formula; null when denom 0)
    a.pass_accuracy_pct,
    a.duels_won_pct,
    a.dribbles_success_pct,
    a.save_pct,
    -- year-over-year (domestic only; the player's primary club that season; NULL
    -- otherwise / when the prior season at that club is absent). CPO metric set 2026-07-03.
    y.yoy_appearances_cutoff,
    y.goals_this_season,
    y.goals_prev_season,
    y.goals_delta_yoy,
    y.assists_this_season,
    y.assists_prev_season,
    y.assists_delta_yoy,
    y.shots_on_goal_player_this_season,
    y.shots_on_goal_player_prev_season,
    y.shots_on_goal_player_delta_yoy,
    y.key_passes_this_season,
    y.key_passes_prev_season,
    y.key_passes_delta_yoy,
    y.defensive_actions_this_season,
    y.defensive_actions_prev_season,
    y.defensive_actions_delta_yoy,
    -- prior-season FULL totals: the "how big was last season" anchor for the pace-matched
    -- deltas above (context only, no delta-vs-full; NULL when the prior season is absent).
    y.appearances_prev_full,
    y.goals_prev_season_full,
    y.assists_prev_season_full,
    y.shots_on_goal_player_prev_season_full,
    y.key_passes_prev_season_full,
    y.defensive_actions_prev_season_full,
    -- contribution-share (goal involvements as a share of the club's whole-season goals; the player's
    -- primary club that season; NULL where absent). CPO metric definition 2026-07-03.
    c.scorer_points,
    c.team_goals_season,
    c.contribution_share,
    -- The season this player's page opens on (#846). Exactly one row per player is true: the most
    -- recent CLUB season, preferring a domestic league over a cup, and falling back to the most
    -- recent season of any kind for a player with no club football at all. Scoped to club because
    -- #848 made the three main tabs club-only; on pure recency a player who has just played a
    -- tournament opens on it, which is why M. Rogers opened on World Cup 2026 with England rather
    -- than the Premier League with Aston Villa. Last in the list because ST06 puts calculations
    -- after simple targets.
    row_number() over (
        partition by a.player_sk
        order by
            case when ct.entity_type = 'club' then 0 else 1 end asc,
            case when reg.competition_type = 'domestic_league' then 0 else 1 end asc,
            a.season_api_year desc
    ) = 1 as is_featured_season
from season as a
left join players as p
    on a.player_sk = p.player_sk
left join modal_position as mp
    on
        a.player_sk = mp.player_sk
        and a.season_sk = mp.season_sk
left join team_affiliation as ta
    on
        a.player_sk = ta.player_sk
        and a.league_code = ta.league_code
        and a.season_api_year = ta.season_api_year
left join teams as t
    on ta.team_sk = t.team_sk
left join yoy as y
    on
        a.player_sk = y.player_sk
        and ta.team_sk = y.team_sk
        and a.league_code = y.league_code
        and a.season_api_year = y.season_api_year
left join contribution as c
    on
        a.player_sk = c.player_sk
        and ta.team_sk = c.team_sk
        and a.season_sk = c.season_sk
left join registry as reg
    on a.league_code = reg.league_code
left join types as ct
    on reg.competition_type = ct.competition_type
