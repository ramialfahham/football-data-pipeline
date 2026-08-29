{{ config(materialized='table') }}

{#
  Full-season team insights for the latest season_api_year per league_code.
  Same metric depth as matchday form; grain one row per team. Use when there is no upcoming
  round (off-season) or before matchday 1 of the next season.
#}

with import_int_team_season__metrics as (
    select * from {{ ref('int_team_season__metrics') }}
),

latest_season_per_league as (
    select
        league_code,
        max(season_api_year) as season_api_year
    from import_int_team_season__metrics
    group by league_code
),

latest_season_metrics as (
    select m.*
    from import_int_team_season__metrics as m
    inner join latest_season_per_league as ls
        on
            m.league_code = ls.league_code
            and m.season_api_year = ls.season_api_year
),

dim_team as (
    select * from {{ ref('dim_team') }}
),

mart_team_season as (
    select * from {{ ref('mart_team_season') }}
)

select
    m.team_season_sk,
    m.team_sk,
    m.season_sk,
    m.league_sk,
    m.league_code,
    m.season_api_year,
    t.team_name,
    t.team_code,
    t.team_country,
    t.team_logo_url,
    ts.played,
    ts.wins,
    ts.draws,
    ts.losses,
    ts.goals_for,
    ts.goals_against,
    ts.goal_diff,
    ts.points,
    ts.clean_sheets,
    ts.latest_rank,
    ts.latest_form,
    ts.standings_group_description,
    m.season_games_played,
    m.season_matchdays_used,
    m.stat_coverage_season_games,
    m.points_won_sum_season,
    m.goals_for_sum_season,
    m.goals_against_sum_season,
    m.total_shots_sum_season,
    m.opponent_total_shots_sum_season,
    m.shots_inside_box_sum_season,
    m.shots_on_goal_sum_season,
    m.corner_kicks_sum_season,
    m.opponent_corner_kicks_sum_season,
    m.passes_accurate_sum_season,
    m.passes_total_sum_season,
    m.goalkeeper_saves_sum_season,
    m.points_capture_pct,
    m.goals_per_match,
    m.goals_against_per_match,
    m.shots_per_match,
    m.shots_share_pct,
    m.shots_inside_box_pct,
    m.shots_on_goal_pct,
    m.finishing_efficiency_pct,
    m.passes_accuracy_pct,
    m.passes_per_match,
    m.corners_per_match,
    m.corners_against_per_match,
    m.saves_pct
from latest_season_metrics as m
inner join dim_team as t on m.team_sk = t.team_sk
left join mart_team_season as ts
    on m.team_season_sk = ts.team_season_sk
