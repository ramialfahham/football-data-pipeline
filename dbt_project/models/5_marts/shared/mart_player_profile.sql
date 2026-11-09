{#
  Player profile (#325). One row per (player, competition-season): the player's season profile a
  player page renders. Mirrors mart_team_profile.

  #480 consolidation: the per-season aggregation now COMPOSES the shared
  int_player_season__metrics (the single player-season rollup) instead of re-aggregating
  fct_fixture_player_stats inline. Identity (dim_player) and the modal season position are assembled here;
  every metric, the GK full-triple (saves_player / shots_on_goal_against_player) included, comes from the
  shared int, which computes each from its catalogue formula. Per-board leaderboard
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
    select
        *,
        coalesce(concat(player_first_name, ' ', player_last_name), player_name) as player_full_name
    from {{ ref('dim_player') }}
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
competitions as (
    select
        league_code,
        competition_type,
        entity_type
    from {{ ref('dim_league') }}
),

page as (
    select * from {{ ref('int_player__page_profile') }}
),

season_labels as (
    select
        season_sk,
        season_label
    from {{ ref('dim_competition_season') }}
),

national_teams as (
    select
        team_sk,
        team_country
    from {{ ref('dim_team') }}
    where is_national_team
),

-- Players with a page who share their full name with another at their current club: the page
-- title tells them apart.
shared_names as (
    select
        pg.player_sk,
        count(*) over (partition by pl.player_full_name, pg.current_club_team_sk) > 1 as shares_name_at_club
    from page as pg
    inner join players as pl
        on pg.player_sk = pl.player_sk
    where
        pg.has_player_page
        and pg.current_club_team_sk is not null
        and pl.player_full_name is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['a.player_sk', 'a.season_sk']) }}
        as player_season_sk,
    a.player_sk,
    a.season_sk,
    a.league_sk,
    a.league_code,
    a.season_api_year,
    sl.season_label,
    reg.competition_type,
    reg.entity_type,
    -- identity + descriptors (not catalogue metrics)
    p.player_name,
    p.player_first_name,
    p.player_last_name,
    p.player_full_name,
    date_diff(current_date(), p.player_birth_date, year)
    - if(format_date('%m%d', current_date()) < format_date('%m%d', p.player_birth_date), 1, 0) as player_age,
    p.player_nationality,
    nt.team_sk as nationality_team_sk,
    p.player_birth_date,
    p.player_birth_place,
    p.player_birth_country,
    p.player_height,
    p.player_weight,
    p.player_position,
    p.player_photo_url,
    mp.position_code,
    -- the Player page's choices, one set per player, the same on each of the player's rows
    pg.position_group,
    pg.has_club_tab,
    pg.has_national_team_tab,
    pg.national_team_sk,
    pg.featured_team_sk,
    pg.current_club_team_sk,
    cc.team_name as current_club_name,
    cc.team_logo_url as current_club_logo_url,
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
    a.goals_player,
    a.goals_penalty_player,
    a.goals_open_play_player,
    a.assists_player,
    a.shots_on_goal_player,
    a.passes_player,
    a.passes_key_player,
    a.passes_accurate_player,
    a.ball_actions_player,
    a.tackles_player,
    a.interceptions_player,
    a.blocks_player,
    a.duels_player,
    a.duels_won_player,
    a.dribbles_attempts_player,
    a.dribbles_success_player,
    a.dribbles_past_player,
    a.offsides_player,
    a.cards_yellow_player,
    a.cards_red_player,
    a.penalty_won_player,
    a.penalty_committed_player,
    -- GK atomics (GAP-12): the save full-triple — saves_player of shots faced
    a.saves_player,
    a.shots_on_goal_against_player,
    -- catalogue ratio metrics (catalogue formula; null when denom 0)
    a.passes_accuracy_player_pct,
    a.duels_won_player_pct,
    a.dribbles_success_player_pct,
    a.saves_player_pct,
    -- year-over-year (domestic only; the player's primary club that season; NULL
    -- otherwise / when the prior season at that club is absent).
    y.yoy_appearances_cutoff,
    y.goals_player_this_season,
    y.goals_player_prev_season,
    y.goals_player_delta_yoy,
    y.assists_player_this_season,
    y.assists_player_prev_season,
    y.assists_player_delta_yoy,
    y.shots_on_goal_player_this_season,
    y.shots_on_goal_player_prev_season,
    y.shots_on_goal_player_delta_yoy,
    y.passes_key_player_this_season,
    y.passes_key_player_prev_season,
    y.passes_key_player_delta_yoy,
    y.defensive_actions_player_this_season,
    y.defensive_actions_player_prev_season,
    y.defensive_actions_player_delta_yoy,
    -- prior-season FULL totals: the "how big was last season" anchor for the pace-matched
    -- deltas above (context only, no delta-vs-full; NULL when the prior season is absent).
    y.appearances_prev_full,
    y.goals_player_prev_season_full,
    y.assists_player_prev_season_full,
    y.shots_on_goal_player_prev_season_full,
    y.passes_key_player_prev_season_full,
    y.defensive_actions_player_prev_season_full,
    -- contribution-share (goal involvements as a share of the club's whole-season goals; the player's
    -- primary club that season; NULL where absent).
    c.scorer_points_player,
    c.team_goals_season,
    c.contribution_player_pct,
    -- The season this player's page opens on: int_player__page_profile chooses it.
    coalesce(a.season_sk = pg.featured_season_sk, false) as is_featured_season,
    coalesce(pg.has_player_page, false) as has_player_page,
    coalesce(sn.shares_name_at_club, false) as shares_name_at_club
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
left join competitions as reg
    on a.league_code = reg.league_code
left join page as pg
    on a.player_sk = pg.player_sk
left join season_labels as sl
    on a.season_sk = sl.season_sk
left join teams as cc
    on pg.current_club_team_sk = cc.team_sk
left join national_teams as nt
    on p.player_nationality = nt.team_country
left join shared_names as sn
    on a.player_sk = sn.player_sk
