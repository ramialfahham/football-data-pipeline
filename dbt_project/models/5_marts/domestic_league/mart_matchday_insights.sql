{{ config(materialized='view') }}

{#
  Wide fixture-preview mart — one row per upcoming fixture (next round per league).

  Reads mart_team_momentum as the form source (same-layer ref — deliberate: this mart
  is a wide presentation pivot of the normalized momentum mart for the Pages UI consumer;
  see dbt_project/docs/layering.md §cross-layer-consumption-rule). Fixture metadata
  and team/league attributes come from core dims. League rank = the team's position in
  its own competition+season table from mart_standings (same-layer ref like the momentum
  source above). Shown only where a single round-robin table applies: null for knockout
  rounds (is_knockout_round) and for overlapping-table leagues where a team has more than
  one section that season (e.g. Argentina).

  Replaces: int_matchday__upcoming_round_fixtures + int_matchday__team_form_metrics
            (old form-window intermediates, retired in this PR).

  Grain: one row per upcoming fixture on the earliest not-started round per
  (league_code, season_api_year). Slice by league_code at export or in the app.
#}

with momentum_home as (
    select * from {{ ref('mart_team_momentum') }}
    where is_home = true
),

momentum_away as (
    select * from {{ ref('mart_team_momentum') }}
    where is_home = false
),

fixtures as (
    select
        fixture_sk,
        fixture_api_id,
        league_sk,
        season_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year,
        fixture_date,
        kickoff_datetime,
        round_name,
        status_short
    from {{ ref('fct_fixture') }}
),

dim_team as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
),

dim_league as (
    select
        league_sk,
        league_name
    from {{ ref('dim_league') }}
),

-- Phase-relevant standing rank (single-table + knockout guards) now lives in
-- mart_fixture_standing_context — the single source shared with the v2 fixtures
-- export, keyed per (upcoming fixture, team). Same-layer ref like the momentum
-- source above. The knockout suppression is applied inside that mart, so
-- league_rank is read straight through here.
standing_context as (
    select
        fixture_sk,
        team_sk,
        league_rank
    from {{ ref('mart_fixture_standing_context') }}
),

-- Earliest not-started round per (league_code, season_api_year)
upcoming_candidates as (
    select *
    from fixtures
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

next_round as (
    select
        league_code,
        season_api_year,
        round_name
    from upcoming_candidates
    qualify row_number() over (
        partition by league_code, season_api_year
        order by fixture_date asc, kickoff_datetime asc
    ) = 1
),

next_round_fixtures as (
    select
        uc.*,
        safe_cast(regexp_extract(uc.round_name, r'(\d+)$') as int64)
            as upcoming_round_order
    from upcoming_candidates as uc
    inner join next_round as nr
        on
            uc.league_code = nr.league_code
            and uc.season_api_year = nr.season_api_year
            and uc.round_name = nr.round_name
),

matchday_fixture_count as (
    select
        league_code,
        season_api_year,
        round_name,
        count(*) as upcoming_matchday_fixture_count
    from next_round_fixtures
    group by league_code, season_api_year, round_name
)

select
    f.fixture_sk,
    f.fixture_api_id,
    f.league_sk,
    f.season_sk,
    f.league_code,
    f.season_api_year,
    f.fixture_date,
    f.kickoff_datetime,
    f.round_name,
    f.upcoming_round_order,
    mfc.upcoming_matchday_fixture_count,
    f.home_team_sk,
    home_dt.team_name as home_team_name,
    home_dt.team_logo_url as home_team_logo_url,
    f.away_team_sk,
    away_dt.team_name as away_team_name,
    away_dt.team_logo_url as away_team_logo_url,
    l.league_name,
    -- league_rank is phase-relevant already (knockout/overlapping → null) from
    -- mart_fixture_standing_context; read straight through.
    home_st.league_rank as home_league_rank,
    away_st.league_rank as away_league_rank,
    -- home form window (from mart_team_momentum). Rates stay null when a team has
    -- no finished matches in the window.
    mh.goals_per_match as home_goals_per_match_recent,
    mh.goals_against_per_match as home_goals_against_per_match_recent,
    mh.shots_per_match as home_shots_per_match_recent,
    mh.shot_accuracy as home_shot_accuracy_recent,
    mh.danger_zone_ratio as home_danger_zone_ratio_recent,
    mh.finishing_efficiency as home_finishing_efficiency_recent,
    mh.passes_per_match as home_passes_per_match_recent,
    mh.pass_accuracy as home_pass_accuracy_recent,
    mh.corners_per_match as home_corners_per_match_recent,
    mh.corners_against_per_match as home_corners_against_per_match_recent,
    mh.saves_pct as home_saves_pct_recent,
    -- away form window (from mart_team_momentum).
    ma.goals_per_match as away_goals_per_match_recent,
    ma.goals_against_per_match as away_goals_against_per_match_recent,
    ma.shots_per_match as away_shots_per_match_recent,
    ma.shot_accuracy as away_shot_accuracy_recent,
    ma.danger_zone_ratio as away_danger_zone_ratio_recent,
    ma.finishing_efficiency as away_finishing_efficiency_recent,
    ma.passes_per_match as away_passes_per_match_recent,
    ma.pass_accuracy as away_pass_accuracy_recent,
    ma.corners_per_match as away_corners_per_match_recent,
    ma.corners_against_per_match as away_corners_against_per_match_recent,
    ma.saves_pct as away_saves_pct_recent,
    -- form games/points: 0 (not null) when a team has no finished matches in the
    -- window. coalesce calculations sort after the simple columns above (ST06).
    coalesce(mh.games_in_window, 0) as home_form_games_played,
    coalesce(mh.points_won, 0) as home_points_won_sum_form,
    coalesce(ma.games_in_window, 0) as away_form_games_played,
    coalesce(ma.points_won, 0) as away_points_won_sum_form,
    -- WC form-context label flags (GAP-18): true when the side's W1 window is the qualifier
    -- window (window_type='qualifiers'). The live formContextLabel UI reads these EXACT field
    -- names to pick "all qualifying matches" vs "all World Cup matches so far" — the names are
    -- pinned by the published UI contract, a CPO-approved exception to the is_/has_ boolean
    -- convention (2026-06-16). coalesce keeps them boolean (never null) for the no-window case.
    -- The mart surfaces one round per league (next_round), so under normal scheduling both sides
    -- of a fixture share the same window phase and the UI's both-sides check is unambiguous (CPO
    -- accepted this dependency over per-side labels, 2026-06-16).
    coalesce(mh.window_type = 'qualifiers', false) as home_form_from_qualifiers,
    coalesce(ma.window_type = 'qualifiers', false) as away_form_from_qualifiers
from next_round_fixtures as f
left join matchday_fixture_count as mfc
    on
        f.league_code = mfc.league_code
        and f.season_api_year = mfc.season_api_year
        and f.round_name = mfc.round_name
left join dim_team as home_dt
    on f.home_team_sk = home_dt.team_sk
left join dim_team as away_dt
    on f.away_team_sk = away_dt.team_sk
left join dim_league as l
    on f.league_sk = l.league_sk
left join momentum_home as mh
    on
        f.fixture_sk = mh.upcoming_fixture_sk
        and f.home_team_sk = mh.team_sk
left join momentum_away as ma
    on
        f.fixture_sk = ma.upcoming_fixture_sk
        and f.away_team_sk = ma.team_sk
left join standing_context as home_st
    on
        f.fixture_sk = home_st.fixture_sk
        and f.home_team_sk = home_st.team_sk
left join standing_context as away_st
    on
        f.fixture_sk = away_st.fixture_sk
        and f.away_team_sk = away_st.team_sk
order by f.league_code asc, f.fixture_date asc, f.kickoff_datetime asc, f.fixture_sk asc
