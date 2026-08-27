{{ config(materialized='view') }}

{#
  W2 season-record mart — team. One row per upcoming fixture side: the team's cumulative
  record in the fixture's own competition this season (the number shown beside W1 momentum).

  COMPOSES int_team_season__metrics (the whole-season rollup) — the same "marts reuse the
  rollup, never recompute" pattern as mart_team_season / _profile / _insights (#500 PR1). The
  whole-season rollup over finished matches IS the season-to-date record, so the metrics are
  taken straight from it (renamed off the `_season` suffix); no formula lives here. For each
  upcoming fixture side we take the team's row for the fixture's (league_code, season_api_year);
  if the team has not played in that competition this season yet (before phase), we fall back to
  the same competition's previous season (window_type = 'prev_season').

  Grain: (upcoming_fixture_sk, team_sk).
#}

with upcoming as (
    select
        fixture_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

sides as (
    select
        fixture_sk as upcoming_fixture_sk,
        home_team_sk as team_sk,
        league_code,
        season_api_year,
        true as is_home
    from upcoming

    union all

    select
        fixture_sk as upcoming_fixture_sk,
        away_team_sk as team_sk,
        league_code,
        season_api_year,
        false as is_home
    from upcoming
),

season_metrics as (
    select * from {{ ref('int_team_season__metrics') }}
),

-- Match each side to its team-season rollup: the fixture's own season (priority 1) or, before the
-- team has played that competition this season, the previous season (priority 2). Metrics come
-- straight from the rollup (rename `_season` → display name); nothing is recomputed.
matched as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        s.league_code,
        s.is_home,
        m.entity_type,
        m.season_api_year,
        m.season_games_played as games_played,
        m.games_with_team_stats,
        m.points_won_sum_season as points_won,
        m.wins_sum_season as wins,
        m.draws_sum_season as draws,
        m.losses_sum_season as losses,
        m.clean_sheets_sum_season as clean_sheets,
        m.goals_per_match,
        m.goals_against_per_match,
        m.shots_per_match,
        m.shot_accuracy,
        m.danger_zone_ratio,
        m.shots_on_goal_per_match,
        m.finishing_efficiency,
        m.passes_per_match,
        m.pass_accuracy,
        m.corners_per_match,
        m.corners_against_per_match,
        m.saves_pct,
        m.key_passes_per_match,
        m.tackles_per_match,
        m.interceptions_per_match,
        m.blocks_per_match,
        m.defensive_actions_per_match,
        m.duels_per_match,
        m.duels_won_pct,
        case
            when m.season_api_year = s.season_api_year then 'season_to_date'
            else 'prev_season'
        end as window_type,
        case when m.season_api_year = s.season_api_year then 1 else 2 end as priority
    from sides as s
    inner join season_metrics as m
        on
            s.team_sk = m.team_sk
            and s.league_code = m.league_code
            and m.season_api_year in (s.season_api_year, s.season_api_year - 1)
),

chosen as (
    select *
    from matched
    qualify row_number() over (
        partition by upcoming_fixture_sk, team_sk
        order by priority asc
    ) = 1
)

select
    upcoming_fixture_sk,
    team_sk,
    league_code,
    entity_type,
    season_api_year,
    window_type,
    games_played,
    games_with_team_stats,
    is_home,
    points_won,
    -- W/D/L counts (the W2 form display — pills misrepresent a season window)
    wins,
    draws,
    losses,
    clean_sheets,
    goals_per_match,
    goals_against_per_match,
    shots_per_match,
    shot_accuracy,
    danger_zone_ratio,
    shots_on_goal_per_match,
    finishing_efficiency,
    passes_per_match,
    pass_accuracy,
    corners_per_match,
    corners_against_per_match,
    saves_pct,
    key_passes_per_match,
    tackles_per_match,
    interceptions_per_match,
    blocks_per_match,
    defensive_actions_per_match,
    duels_per_match,
    duels_won_pct
from chosen
