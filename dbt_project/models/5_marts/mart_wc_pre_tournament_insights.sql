{{ config(materialized='table') }}

{#
  WC tournament participants: pre-tournament (qualifier) team insights for the app.
  Grain: one row per team_sk in the current WC season on fct_fixture.
  UI contract: display a metric only when the matching is_*_complete flag is true.
#}

with import_int_wc__pre_tournament_team_metrics as (
    select * from {{ ref('int_wc__pre_tournament_team_metrics') }}
),

dim_team as (
    select
        team_sk,
        any_value(team_name) as team_name,
        any_value(team_code) as team_code,
        any_value(team_country) as team_country,
        any_value(team_logo_url) as team_logo_url
    from {{ ref('dim_team') }}
    group by team_sk
)

select
    m.team_sk,
    m.tournament_league_code as league_code,
    m.tournament_season_api_year as season_api_year,
    t.team_name,
    t.team_code,
    t.team_country,
    t.team_logo_url,
    m.qualifier_games_played,
    m.qualifier_matchdays_used,
    m.stat_coverage_qualifier_games,
    m.points_won_sum_pretournament,
    m.goals_for_sum_pretournament,
    m.goals_against_sum_pretournament,
    m.total_shots_sum_pretournament,
    m.opponent_total_shots_sum_pretournament,
    m.shots_inside_box_sum_pretournament,
    m.shots_on_goal_sum_pretournament,
    m.corner_kicks_sum_pretournament,
    m.opponent_corner_kicks_sum_pretournament,
    m.passes_accurate_sum_pretournament,
    m.passes_total_sum_pretournament,
    m.goalkeeper_saves_sum_pretournament,
    m.points_capture_pretournament,
    m.goals_per_match_pretournament,
    m.goals_against_per_match_pretournament,
    m.shots_per_match_pretournament,
    m.shot_share_pretournament,
    m.danger_zone_ratio_pretournament,
    m.shot_accuracy_pretournament,
    m.finishing_efficiency_pretournament,
    m.pass_accuracy_pretournament,
    m.passes_per_match_pretournament,
    m.corner_kicks_per_match_pretournament,
    m.corners_conceded_per_match_pretournament,
    m.save_ratio_pretournament,
    m.is_points_capture_complete,
    m.is_goals_per_match_complete,
    m.is_goals_against_per_match_complete,
    m.is_shots_per_match_complete,
    m.is_shot_share_complete,
    m.is_danger_zone_ratio_complete,
    m.is_shot_accuracy_complete,
    m.is_finishing_efficiency_complete,
    m.is_pass_accuracy_complete,
    m.is_passes_per_match_complete,
    m.is_corner_kicks_per_match_complete,
    m.is_corners_conceded_per_match_complete,
    m.is_save_ratio_complete
from import_int_wc__pre_tournament_team_metrics as m
inner join dim_team as t
    on m.team_sk = t.team_sk
