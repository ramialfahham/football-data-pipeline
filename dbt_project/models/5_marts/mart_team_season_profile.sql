{{ config(materialized='table') }}

{#
  Full-season advanced team profile for the latest completed (or in-progress) season per league.
  Same metric depth as matchday form; grain one row per team in that league's latest season_api_year.
  Use when there is no upcoming round (off-season) or before matchday 1 of the next season.
#}

with import_int_team_season__profile_metrics as (
    select * from {{ ref('int_team_season__profile_metrics') }}
),

latest_season_per_league as (
    select
        league_code,
        max(season_api_year) as season_api_year
    from import_int_team_season__profile_metrics
    group by league_code
),

latest_profile as (
    select pm.*
    from import_int_team_season__profile_metrics as pm
    inner join latest_season_per_league as ls
        on
            pm.league_code = ls.league_code
            and pm.season_api_year = ls.season_api_year
),

dim_team as (
    select * from {{ ref('dim_team') }}
),

mart_team_season as (
    select * from {{ ref('mart_team_season') }}
)

select
    lp.team_season_sk,
    lp.team_sk,
    lp.season_sk,
    lp.league_sk,
    lp.league_code,
    lp.season_api_year,
    t.team_name,
    t.team_code,
    t.team_country,
    t.team_logo_url,
    mts.played,
    mts.wins,
    mts.draws,
    mts.losses,
    mts.goals_for,
    mts.goals_against,
    mts.goal_diff,
    mts.points,
    mts.clean_sheets,
    mts.latest_rank,
    mts.latest_form,
    mts.standings_group_description,
    lp.season_games_played,
    lp.season_matchdays_used,
    lp.stat_coverage_season_games,
    lp.points_won_sum_season,
    lp.goals_for_sum_season,
    lp.goals_against_sum_season,
    lp.total_shots_sum_season,
    lp.opponent_total_shots_sum_season,
    lp.shots_inside_box_sum_season,
    lp.shots_on_goal_sum_season,
    lp.corner_kicks_sum_season,
    lp.opponent_corner_kicks_sum_season,
    lp.passes_accurate_sum_season,
    lp.passes_total_sum_season,
    lp.goalkeeper_saves_sum_season,
    lp.points_capture_season,
    lp.goals_per_match_season,
    lp.goals_against_per_match_season,
    lp.shots_per_match_season,
    lp.shot_share_season,
    lp.danger_zone_ratio_season,
    lp.shot_accuracy_season,
    lp.finishing_efficiency_season,
    lp.pass_accuracy_season,
    lp.passes_per_match_season,
    lp.corner_kicks_per_match_season,
    lp.corners_conceded_per_match_season,
    lp.save_ratio_season
from latest_profile as lp
inner join dim_team as t on lp.team_sk = t.team_sk
left join mart_team_season as mts
    on lp.team_season_sk = mts.team_season_sk
