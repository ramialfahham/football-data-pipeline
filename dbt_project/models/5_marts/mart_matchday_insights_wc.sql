{{ config(materialized='view') }}

{#
  FIFA World Cup (WC) matchday preview mart: same column contract as mart_matchday_insights.
  Pre-tournament: form from mart_wc_pre_tournament_insights (qualifier window, single source of truth).
  After a team's first finished WC leg in the season: last-five WC legs via int_matchday__team_form_metrics.
#}

with import_int_matchday__upcoming_round_fixtures as (
    select * from {{ ref('int_matchday__upcoming_round_fixtures') }}
    where league_code = 'WC'
),

import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

import_int_matchday__team_form_metrics as (
    select * from {{ ref('int_matchday__team_form_metrics') }}
),

mart_wc_pre_tournament_insights as (
    select * from {{ ref('mart_wc_pre_tournament_insights') }}
),

mart_team_season as (
    select * from {{ ref('mart_team_season') }}
),

team_form_metrics as (
    select * from import_int_matchday__team_form_metrics
),

home_wc_tournament_legs_before as (
    select
        um.fixture_sk,
        um.home_team_sk as team_sk,
        count(*) as n_wc_tournament_before
    from import_int_matchday__upcoming_round_fixtures as um
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            um.home_team_sk = fwo.team_sk
            and fwo.league_code = 'WC'
            and um.season_api_year = fwo.season_api_year
            and (
                um.kickoff_datetime > fwo.kickoff_datetime
                or (
                    um.kickoff_datetime = fwo.kickoff_datetime
                    and um.fixture_sk > fwo.fixture_sk
                )
            )
    group by um.fixture_sk, um.home_team_sk
),

away_wc_tournament_legs_before as (
    select
        um.fixture_sk,
        um.away_team_sk as team_sk,
        count(*) as n_wc_tournament_before
    from import_int_matchday__upcoming_round_fixtures as um
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            um.away_team_sk = fwo.team_sk
            and fwo.league_code = 'WC'
            and um.season_api_year = fwo.season_api_year
            and (
                um.kickoff_datetime > fwo.kickoff_datetime
                or (
                    um.kickoff_datetime = fwo.kickoff_datetime
                    and um.fixture_sk > fwo.fixture_sk
                )
            )
    group by um.fixture_sk, um.away_team_sk
),

home_form_matchday as (
    select
        fixture_sk,
        team_sk as home_team_sk,
        form_season_api_year,
        form_games_played,
        form_matchdays_used,
        stat_coverage_form_games,
        points_won_sum_form,
        goals_for_sum_form,
        goals_against_sum_form,
        total_shots_sum_form,
        opponent_total_shots_sum_form,
        shots_inside_box_sum_form,
        shots_on_goal_sum_form,
        corner_kicks_sum_form,
        opponent_corner_kicks_sum_form,
        passes_accurate_sum_form,
        passes_total_sum_form,
        goalkeeper_saves_sum_form,
        points_capture_recent,
        goals_per_match_recent,
        goals_against_per_match_recent,
        shots_per_match_recent,
        shot_share_recent,
        danger_zone_ratio_recent,
        shot_accuracy_recent,
        finishing_efficiency_recent,
        pass_accuracy_recent,
        passes_per_match_recent,
        corner_kicks_per_match_recent,
        corners_conceded_per_match_recent,
        save_ratio_recent
    from team_form_metrics
),

away_form_matchday as (
    select
        fixture_sk,
        team_sk as away_team_sk,
        form_season_api_year,
        form_games_played,
        form_matchdays_used,
        stat_coverage_form_games,
        points_won_sum_form,
        goals_for_sum_form,
        goals_against_sum_form,
        total_shots_sum_form,
        opponent_total_shots_sum_form,
        shots_inside_box_sum_form,
        shots_on_goal_sum_form,
        corner_kicks_sum_form,
        opponent_corner_kicks_sum_form,
        passes_accurate_sum_form,
        passes_total_sum_form,
        goalkeeper_saves_sum_form,
        points_capture_recent,
        goals_per_match_recent,
        goals_against_per_match_recent,
        shots_per_match_recent,
        shot_share_recent,
        danger_zone_ratio_recent,
        shot_accuracy_recent,
        finishing_efficiency_recent,
        pass_accuracy_recent,
        passes_per_match_recent,
        corner_kicks_per_match_recent,
        corners_conceded_per_match_recent,
        save_ratio_recent
    from team_form_metrics
),

final as (
    select
        um.fixture_sk,
        um.fixture_api_id,
        um.league_sk,
        um.season_sk,
        um.league_code,
        um.season_api_year,
        um.fixture_date,
        um.kickoff_datetime,
        um.round_name,
        um.upcoming_round_order,
        um.home_team_sk,
        um.home_team_name,
        um.away_team_sk,
        um.away_team_name,
        um.upcoming_matchday_fixture_count,
        home_pt.team_logo_url as home_team_logo_url,
        away_pt.team_logo_url as away_team_logo_url,
        home_ts.latest_rank as home_league_rank,
        away_ts.latest_rank as away_league_rank,
        home_ts.standings_group_description as home_standings_group_description,
        away_ts.standings_group_description as away_standings_group_description,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.season_api_year
            else hfm.form_season_api_year
        end as home_form_season_api_year,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.qualifier_games_played
            else hfm.form_games_played
        end as home_form_games_played,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.qualifier_matchdays_used
            else hfm.form_matchdays_used
        end as home_form_matchdays_used,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.stat_coverage_qualifier_games
            else hfm.stat_coverage_form_games
        end as home_stat_coverage_form_games,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.points_won_sum_pretournament
            else hfm.points_won_sum_form
        end as home_points_won_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.goals_for_sum_pretournament
            else hfm.goals_for_sum_form
        end as home_goals_for_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.goals_against_sum_pretournament
            else hfm.goals_against_sum_form
        end as home_goals_against_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.total_shots_sum_pretournament
            else hfm.total_shots_sum_form
        end as home_total_shots_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.opponent_total_shots_sum_pretournament
            else hfm.opponent_total_shots_sum_form
        end as home_opponent_total_shots_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.shots_inside_box_sum_pretournament
            else hfm.shots_inside_box_sum_form
        end as home_shots_inside_box_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.shots_on_goal_sum_pretournament
            else hfm.shots_on_goal_sum_form
        end as home_shots_on_goal_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.corner_kicks_sum_pretournament
            else hfm.corner_kicks_sum_form
        end as home_corner_kicks_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.opponent_corner_kicks_sum_pretournament
            else hfm.opponent_corner_kicks_sum_form
        end as home_opponent_corner_kicks_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.passes_accurate_sum_pretournament
            else hfm.passes_accurate_sum_form
        end as home_passes_accurate_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.passes_total_sum_pretournament
            else hfm.passes_total_sum_form
        end as home_passes_total_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.goalkeeper_saves_sum_pretournament
            else hfm.goalkeeper_saves_sum_form
        end as home_goalkeeper_saves_sum_form,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.points_capture_pretournament
            else hfm.points_capture_recent
        end as home_points_capture_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.goals_per_match_pretournament
            else hfm.goals_per_match_recent
        end as home_goals_per_match_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.goals_against_per_match_pretournament
            else hfm.goals_against_per_match_recent
        end as home_goals_against_per_match_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.shots_per_match_pretournament
            else hfm.shots_per_match_recent
        end as home_shots_per_match_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.shot_share_pretournament
            else hfm.shot_share_recent
        end as home_shot_share_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.danger_zone_ratio_pretournament
            else hfm.danger_zone_ratio_recent
        end as home_danger_zone_ratio_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.shot_accuracy_pretournament
            else hfm.shot_accuracy_recent
        end as home_shot_accuracy_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.finishing_efficiency_pretournament
            else hfm.finishing_efficiency_recent
        end as home_finishing_efficiency_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.pass_accuracy_pretournament
            else hfm.pass_accuracy_recent
        end as home_pass_accuracy_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.passes_per_match_pretournament
            else hfm.passes_per_match_recent
        end as home_passes_per_match_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.corner_kicks_per_match_pretournament
            else hfm.corner_kicks_per_match_recent
        end as home_corner_kicks_per_match_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.corners_conceded_per_match_pretournament
            else hfm.corners_conceded_per_match_recent
        end as home_corners_conceded_per_match_recent,
        case
            when coalesce(hwb.n_wc_tournament_before, 0) = 0 then home_pt.save_ratio_pretournament
            else hfm.save_ratio_recent
        end as home_save_ratio_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.season_api_year
            else afm.form_season_api_year
        end as away_form_season_api_year,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.qualifier_games_played
            else afm.form_games_played
        end as away_form_games_played,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.qualifier_matchdays_used
            else afm.form_matchdays_used
        end as away_form_matchdays_used,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.stat_coverage_qualifier_games
            else afm.stat_coverage_form_games
        end as away_stat_coverage_form_games,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.points_won_sum_pretournament
            else afm.points_won_sum_form
        end as away_points_won_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.goals_for_sum_pretournament
            else afm.goals_for_sum_form
        end as away_goals_for_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.goals_against_sum_pretournament
            else afm.goals_against_sum_form
        end as away_goals_against_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.total_shots_sum_pretournament
            else afm.total_shots_sum_form
        end as away_total_shots_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.opponent_total_shots_sum_pretournament
            else afm.opponent_total_shots_sum_form
        end as away_opponent_total_shots_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.shots_inside_box_sum_pretournament
            else afm.shots_inside_box_sum_form
        end as away_shots_inside_box_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.shots_on_goal_sum_pretournament
            else afm.shots_on_goal_sum_form
        end as away_shots_on_goal_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.corner_kicks_sum_pretournament
            else afm.corner_kicks_sum_form
        end as away_corner_kicks_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.opponent_corner_kicks_sum_pretournament
            else afm.opponent_corner_kicks_sum_form
        end as away_opponent_corner_kicks_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.passes_accurate_sum_pretournament
            else afm.passes_accurate_sum_form
        end as away_passes_accurate_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.passes_total_sum_pretournament
            else afm.passes_total_sum_form
        end as away_passes_total_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.goalkeeper_saves_sum_pretournament
            else afm.goalkeeper_saves_sum_form
        end as away_goalkeeper_saves_sum_form,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.points_capture_pretournament
            else afm.points_capture_recent
        end as away_points_capture_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.goals_per_match_pretournament
            else afm.goals_per_match_recent
        end as away_goals_per_match_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.goals_against_per_match_pretournament
            else afm.goals_against_per_match_recent
        end as away_goals_against_per_match_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.shots_per_match_pretournament
            else afm.shots_per_match_recent
        end as away_shots_per_match_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.shot_share_pretournament
            else afm.shot_share_recent
        end as away_shot_share_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.danger_zone_ratio_pretournament
            else afm.danger_zone_ratio_recent
        end as away_danger_zone_ratio_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.shot_accuracy_pretournament
            else afm.shot_accuracy_recent
        end as away_shot_accuracy_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.finishing_efficiency_pretournament
            else afm.finishing_efficiency_recent
        end as away_finishing_efficiency_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.pass_accuracy_pretournament
            else afm.pass_accuracy_recent
        end as away_pass_accuracy_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.passes_per_match_pretournament
            else afm.passes_per_match_recent
        end as away_passes_per_match_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.corner_kicks_per_match_pretournament
            else afm.corner_kicks_per_match_recent
        end as away_corner_kicks_per_match_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.corners_conceded_per_match_pretournament
            else afm.corners_conceded_per_match_recent
        end as away_corners_conceded_per_match_recent,
        case
            when coalesce(awb.n_wc_tournament_before, 0) = 0 then away_pt.save_ratio_pretournament
            else afm.save_ratio_recent
        end as away_save_ratio_recent,
        coalesce(hwb.n_wc_tournament_before, 0) = 0 as home_form_from_qualifiers,
        coalesce(awb.n_wc_tournament_before, 0) = 0 as away_form_from_qualifiers,
        um.league_name
    from import_int_matchday__upcoming_round_fixtures as um
    left join mart_team_season as home_ts
        on
            um.home_team_sk = home_ts.team_sk
            and um.season_sk = home_ts.season_sk
    left join mart_team_season as away_ts
        on
            um.away_team_sk = away_ts.team_sk
            and um.season_sk = away_ts.season_sk
    left join mart_wc_pre_tournament_insights as home_pt
        on um.home_team_sk = home_pt.team_sk
    left join mart_wc_pre_tournament_insights as away_pt
        on um.away_team_sk = away_pt.team_sk
    left join home_wc_tournament_legs_before as hwb
        on
            um.fixture_sk = hwb.fixture_sk
            and um.home_team_sk = hwb.team_sk
    left join away_wc_tournament_legs_before as awb
        on
            um.fixture_sk = awb.fixture_sk
            and um.away_team_sk = awb.team_sk
    left join home_form_matchday as hfm
        on
            um.fixture_sk = hfm.fixture_sk
            and um.home_team_sk = hfm.home_team_sk
    left join away_form_matchday as afm
        on
            um.fixture_sk = afm.fixture_sk
            and um.away_team_sk = afm.away_team_sk
)

select *
from final
order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
