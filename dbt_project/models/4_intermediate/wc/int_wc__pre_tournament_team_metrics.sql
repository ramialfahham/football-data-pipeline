{{ config(materialized='table') }}

{#
  Per WC participant (team_sk): qualifier-window aggregates and per-metric completeness flags.
  Completeness = every leg in int_wc__pre_tournament_qualifier_legs has the raw stats required
  to compute that metric (UI shows values only when is_*_complete).
  Grain: (team_sk).
#}

with import_int_wc__participant_teams as (
    select * from {{ ref('int_wc__participant_teams') }}
),

import_int_wc__pre_tournament_qualifier_legs as (
    select * from {{ ref('int_wc__pre_tournament_qualifier_legs') }}
),

leg_coverage as (
    select
        pt.team_sk,
        pt.league_code as tournament_league_code,
        pt.season_api_year as tournament_season_api_year,
        count(distinct leg.fixture_sk) as qualifier_games_played,
        count(distinct leg.round_name) as qualifier_matchdays_used,
        countif(leg.shots_on_goal is not null) as legs_with_shots_on_goal,
        countif(leg.shots_total is not null) as legs_with_shots_total,
        countif(leg.shots_inside_box is not null) as legs_with_shots_inside_box,
        countif(leg.opponent_total_shots is not null) as legs_with_opponent_shots,
        countif(leg.passes_total is not null) as legs_with_passes_total,
        countif(leg.passes_accurate is not null) as legs_with_passes_accurate,
        countif(leg.corner_kicks is not null) as legs_with_corners,
        countif(leg.opponent_corner_kicks is not null) as legs_with_opp_corners,
        countif(leg.goalkeeper_saves is not null) as legs_with_saves
    from import_int_wc__participant_teams as pt
    left join import_int_wc__pre_tournament_qualifier_legs as leg
        on pt.team_sk = leg.team_sk
    group by pt.team_sk, pt.league_code, pt.season_api_year
),

aggregated as (
    select
        leg.team_sk,
        count(distinct leg.fixture_sk) as qualifier_games_played,
        count(distinct leg.round_name) as qualifier_matchdays_used,
        count(
            distinct case when leg.shots_on_goal is not null then leg.fixture_sk end
        ) as stat_coverage_qualifier_games,
        sum(
            case upper(trim(leg.result))
                when 'W' then 3
                when 'D' then 1
                else 0
            end
        ) as points_won_sum_pretournament,
        sum(leg.goals_for) as goals_for_sum_pretournament,
        sum(leg.goals_against) as goals_against_sum_pretournament,
        sum(leg.shots_total) as total_shots_sum_pretournament,
        sum(leg.opponent_total_shots) as opponent_total_shots_sum_pretournament,
        sum(leg.shots_inside_box) as shots_inside_box_sum_pretournament,
        sum(leg.shots_on_goal) as shots_on_goal_sum_pretournament,
        sum(leg.corner_kicks) as corner_kicks_sum_pretournament,
        sum(leg.opponent_corner_kicks) as opponent_corner_kicks_sum_pretournament,
        sum(leg.passes_accurate) as passes_accurate_sum_pretournament,
        sum(leg.passes_total) as passes_total_sum_pretournament,
        sum(leg.goalkeeper_saves) as goalkeeper_saves_sum_pretournament
    from import_int_wc__pre_tournament_qualifier_legs as leg
    group by leg.team_sk
),

metrics as (
    select
        lc.team_sk,
        lc.tournament_league_code,
        lc.tournament_season_api_year,
        lc.legs_with_shots_on_goal,
        lc.legs_with_shots_total,
        lc.legs_with_shots_inside_box,
        lc.legs_with_opponent_shots,
        lc.legs_with_passes_total,
        lc.legs_with_passes_accurate,
        lc.legs_with_corners,
        lc.legs_with_opp_corners,
        lc.legs_with_saves,
        lc.qualifier_games_played as legs_in_window,
        agg.points_won_sum_pretournament,
        agg.goals_for_sum_pretournament,
        agg.goals_against_sum_pretournament,
        agg.total_shots_sum_pretournament,
        agg.opponent_total_shots_sum_pretournament,
        agg.shots_inside_box_sum_pretournament,
        agg.shots_on_goal_sum_pretournament,
        agg.corner_kicks_sum_pretournament,
        agg.opponent_corner_kicks_sum_pretournament,
        agg.passes_accurate_sum_pretournament,
        agg.passes_total_sum_pretournament,
        agg.goalkeeper_saves_sum_pretournament,
        coalesce(agg.qualifier_games_played, lc.qualifier_games_played, 0) as qualifier_games_played,
        coalesce(agg.qualifier_matchdays_used, lc.qualifier_matchdays_used, 0) as qualifier_matchdays_used,
        coalesce(agg.stat_coverage_qualifier_games, 0) as stat_coverage_qualifier_games
    from leg_coverage as lc
    left join aggregated as agg
        on lc.team_sk = agg.team_sk
)

select
    team_sk,
    tournament_league_code,
    tournament_season_api_year,
    qualifier_games_played,
    qualifier_matchdays_used,
    stat_coverage_qualifier_games,
    points_won_sum_pretournament,
    goals_for_sum_pretournament,
    goals_against_sum_pretournament,
    total_shots_sum_pretournament,
    opponent_total_shots_sum_pretournament,
    shots_inside_box_sum_pretournament,
    shots_on_goal_sum_pretournament,
    corner_kicks_sum_pretournament,
    opponent_corner_kicks_sum_pretournament,
    passes_accurate_sum_pretournament,
    passes_total_sum_pretournament,
    goalkeeper_saves_sum_pretournament,
    safe_divide(points_won_sum_pretournament, 3 * qualifier_games_played) as points_capture_pretournament,
    safe_divide(goals_for_sum_pretournament, qualifier_games_played) as goals_per_match_pretournament,
    safe_divide(goals_against_sum_pretournament, qualifier_games_played) as goals_against_per_match_pretournament,
    safe_divide(total_shots_sum_pretournament, qualifier_games_played) as shots_per_match_pretournament,
    safe_divide(
        total_shots_sum_pretournament,
        nullif(total_shots_sum_pretournament + opponent_total_shots_sum_pretournament, 0)
    ) as shot_share_pretournament,
    safe_divide(shots_inside_box_sum_pretournament, total_shots_sum_pretournament) as danger_zone_ratio_pretournament,
    safe_divide(shots_on_goal_sum_pretournament, total_shots_sum_pretournament) as shot_accuracy_pretournament,
    case
        when shots_on_goal_sum_pretournament is null or shots_on_goal_sum_pretournament = 0 then null
        when goals_for_sum_pretournament > shots_on_goal_sum_pretournament then null
        else safe_divide(goals_for_sum_pretournament, shots_on_goal_sum_pretournament)
    end as finishing_efficiency_pretournament,
    safe_divide(passes_accurate_sum_pretournament, passes_total_sum_pretournament) as pass_accuracy_pretournament,
    safe_divide(passes_total_sum_pretournament, qualifier_games_played) as passes_per_match_pretournament,
    safe_divide(corner_kicks_sum_pretournament, qualifier_games_played) as corner_kicks_per_match_pretournament,
    safe_divide(
        opponent_corner_kicks_sum_pretournament,
        qualifier_games_played
    ) as corners_conceded_per_match_pretournament,
    safe_divide(
        goalkeeper_saves_sum_pretournament,
        nullif(goalkeeper_saves_sum_pretournament + goals_against_sum_pretournament, 0)
    ) as save_ratio_pretournament,
    qualifier_games_played > 0 as is_points_capture_complete,
    qualifier_games_played > 0 as is_goals_per_match_complete,
    qualifier_games_played > 0 as is_goals_against_per_match_complete,
    legs_in_window > 0 and legs_with_shots_total = legs_in_window as is_shots_per_match_complete,
    legs_in_window > 0
    and legs_with_shots_total = legs_in_window
    and legs_with_opponent_shots = legs_in_window as is_shot_share_complete,
    legs_in_window > 0
    and legs_with_shots_total = legs_in_window
    and legs_with_shots_inside_box = legs_in_window as is_danger_zone_ratio_complete,
    legs_in_window > 0
    and legs_with_shots_total = legs_in_window
    and legs_with_shots_on_goal = legs_in_window as is_shot_accuracy_complete,
    legs_in_window > 0
    and legs_with_shots_total = legs_in_window
    and legs_with_shots_on_goal = legs_in_window as is_finishing_efficiency_complete,
    legs_in_window > 0
    and legs_with_passes_total = legs_in_window
    and legs_with_passes_accurate = legs_in_window as is_pass_accuracy_complete,
    legs_in_window > 0 and legs_with_passes_total = legs_in_window as is_passes_per_match_complete,
    legs_in_window > 0 and legs_with_corners = legs_in_window as is_corner_kicks_per_match_complete,
    legs_in_window > 0 and legs_with_opp_corners = legs_in_window as is_corners_conceded_per_match_complete,
    legs_in_window > 0 and legs_with_saves = legs_in_window as is_save_ratio_complete
from metrics
