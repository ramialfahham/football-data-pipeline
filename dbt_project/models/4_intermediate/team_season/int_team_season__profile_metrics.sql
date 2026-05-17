{{ config(materialized='table') }}

{#
  Per (league_code, season_api_year, team_sk) advanced metrics over all finished legs in that season.
  Same sum/rate definitions as int_matchday__team_form_metrics (full window, no five-game cap).
  Grain: (league_code, season_api_year, team_sk). Consumer marts filter to the latest season per league.
#}

with import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

season_legs_dedup as (
    select * except (leg_dedup_rn)
    from (
        select
            *,
            row_number() over (
                partition by league_code, season_api_year, team_sk, fixture_sk
                order by kickoff_datetime desc, fixture_sk desc
            ) as leg_dedup_rn
        from import_int_matchday__finished_fixture_team_leg
    )
    where leg_dedup_rn = 1
),

aggregated_season as (
    select
        league_code,
        season_api_year,
        team_sk,
        any_value(league_sk) as league_sk,
        any_value(season_sk) as season_sk,
        count(distinct fixture_sk) as season_games_played,
        count(distinct round_name) as season_matchdays_used,
        count(distinct case when shots_on_goal is not null then fixture_sk end) as stat_coverage_season_games,
        sum(
            case upper(trim(result))
                when 'W' then 3
                when 'D' then 1
                else 0
            end
        ) as points_won_sum_season,
        sum(goals_for) as goals_for_sum_season,
        sum(goals_against) as goals_against_sum_season,
        sum(shots_total) as total_shots_sum_season,
        sum(opponent_total_shots) as opponent_total_shots_sum_season,
        sum(shots_inside_box) as shots_inside_box_sum_season,
        sum(shots_on_goal) as shots_on_goal_sum_season,
        sum(corner_kicks) as corner_kicks_sum_season,
        sum(opponent_corner_kicks) as opponent_corner_kicks_sum_season,
        sum(passes_accurate) as passes_accurate_sum_season,
        sum(passes_total) as passes_total_sum_season,
        sum(goalkeeper_saves) as goalkeeper_saves_sum_season
    from season_legs_dedup
    group by league_code, season_api_year, team_sk
)

select
    {{ dbt_utils.generate_surrogate_key(['team_sk', 'season_sk']) }} as team_season_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    season_games_played,
    season_matchdays_used,
    stat_coverage_season_games,
    points_won_sum_season,
    goals_for_sum_season,
    goals_against_sum_season,
    total_shots_sum_season,
    opponent_total_shots_sum_season,
    shots_inside_box_sum_season,
    shots_on_goal_sum_season,
    corner_kicks_sum_season,
    opponent_corner_kicks_sum_season,
    passes_accurate_sum_season,
    passes_total_sum_season,
    goalkeeper_saves_sum_season,
    safe_divide(points_won_sum_season, 3 * season_games_played) as points_capture_season,
    safe_divide(goals_for_sum_season, season_games_played) as goals_per_match_season,
    safe_divide(goals_against_sum_season, season_games_played) as goals_against_per_match_season,
    safe_divide(total_shots_sum_season, season_games_played) as shots_per_match_season,
    safe_divide(
        total_shots_sum_season,
        nullif(total_shots_sum_season + opponent_total_shots_sum_season, 0)
    ) as shot_share_season,
    safe_divide(shots_inside_box_sum_season, total_shots_sum_season) as danger_zone_ratio_season,
    safe_divide(shots_on_goal_sum_season, total_shots_sum_season) as shot_accuracy_season,
    case
        when shots_on_goal_sum_season is null or shots_on_goal_sum_season = 0 then null
        when goals_for_sum_season > shots_on_goal_sum_season then null
        else safe_divide(goals_for_sum_season, shots_on_goal_sum_season)
    end as finishing_efficiency_season,
    safe_divide(passes_accurate_sum_season, passes_total_sum_season) as pass_accuracy_season,
    safe_divide(passes_total_sum_season, season_games_played) as passes_per_match_season,
    safe_divide(corner_kicks_sum_season, season_games_played) as corner_kicks_per_match_season,
    safe_divide(opponent_corner_kicks_sum_season, season_games_played) as corners_conceded_per_match_season,
    safe_divide(
        goalkeeper_saves_sum_season,
        nullif(goalkeeper_saves_sum_season + goals_against_sum_season, 0)
    ) as save_ratio_season
from aggregated_season
