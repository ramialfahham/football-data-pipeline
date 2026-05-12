{{ config(materialized='table') }}

{#
  Per (upcoming fixture_sk, team_sk) form aggregates for matchday preview.
  Grain: (fixture_sk, team_sk) where fixture_sk is the upcoming fixture.
#}

with import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

import_int_matchday__upcoming_round_fixtures as (
    select * from {{ ref('int_matchday__upcoming_round_fixtures') }}
),

team_fixture_context as (
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.home_team_sk as team_sk
    from import_int_matchday__upcoming_round_fixtures as um
    union all
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.away_team_sk as team_sk
    from import_int_matchday__upcoming_round_fixtures as um
),

current_season_game_counts as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        count(fwo.fixture_sk) as completed_games_in_current_season
    from team_fixture_context as tfc
    left join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tfc.team_sk = fwo.team_sk
            and tfc.league_code = fwo.league_code
            and tfc.season_api_year = fwo.season_api_year
            and tfc.upcoming_kickoff_datetime > fwo.kickoff_datetime
            and (
                tfc.upcoming_round_order is null
                or fwo.round_order is null
                or tfc.upcoming_round_order > fwo.round_order
            )
    group by tfc.upcoming_fixture_sk, tfc.team_sk
),

team_season_choice as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        tfc.league_code,
        tfc.upcoming_kickoff_datetime,
        tfc.upcoming_round_order,
        case
            when coalesce(cs.completed_games_in_current_season, 0) = 0
                then tfc.season_api_year - 1
            else tfc.season_api_year
        end as form_season_api_year,
        coalesce(cs.completed_games_in_current_season, 0) > 0 as use_current_season
    from team_fixture_context as tfc
    left join current_season_game_counts as cs
        on
            tfc.upcoming_fixture_sk = cs.upcoming_fixture_sk
            and tfc.team_sk = cs.team_sk
),

past_team_matches as (
    select
        tsc.upcoming_fixture_sk,
        tsc.team_sk,
        fwo.fixture_sk,
        fwo.kickoff_datetime,
        fwo.round_name,
        fwo.round_order,
        fwo.goals_for,
        fwo.goals_against,
        fwo.result,
        fwo.shots_on_goal,
        fwo.shots_total,
        fwo.shots_inside_box,
        fwo.corner_kicks,
        fwo.passes_total,
        fwo.passes_accurate,
        fwo.goalkeeper_saves,
        fwo.opponent_total_shots,
        fwo.opponent_corner_kicks,
        tsc.form_season_api_year,
        tsc.use_current_season,
        dense_rank() over (
            partition by tsc.upcoming_fixture_sk, tsc.team_sk
            order by fwo.round_order desc nulls last, fwo.kickoff_datetime desc
        ) as recent_matchday_rank
    from team_season_choice as tsc
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tsc.team_sk = fwo.team_sk
            and tsc.league_code = fwo.league_code
            and tsc.form_season_api_year = fwo.season_api_year
            and tsc.upcoming_kickoff_datetime > fwo.kickoff_datetime
            and (
                not tsc.use_current_season
                or tsc.upcoming_round_order is null
                or fwo.round_order is null
                or tsc.upcoming_round_order > fwo.round_order
            )
),

form_window_matches as (
    select * from past_team_matches
    where not use_current_season or recent_matchday_rank <= 5
),

aggregated_form as (
    select
        upcoming_fixture_sk as fixture_sk,
        team_sk,
        any_value(form_season_api_year) as form_season_api_year,
        count(distinct fixture_sk) as form_games_played,
        count(distinct round_name) as form_matchdays_used,
        count(distinct case when shots_on_goal is not null then fixture_sk end) as stat_coverage_form_games,
        sum(
            case result
                when 'W' then 3
                when 'D' then 1
                else 0
            end
        ) as points_won_sum_form,
        sum(goals_for) as goals_for_sum_form,
        sum(goals_against) as goals_against_sum_form,
        sum(coalesce(shots_total, 0)) as total_shots_sum_form,
        sum(coalesce(opponent_total_shots, 0)) as opponent_total_shots_sum_form,
        sum(coalesce(shots_inside_box, 0)) as shots_inside_box_sum_form,
        sum(coalesce(shots_on_goal, 0)) as shots_on_goal_sum_form,
        sum(coalesce(corner_kicks, 0)) as corner_kicks_sum_form,
        sum(coalesce(opponent_corner_kicks, 0)) as opponent_corner_kicks_sum_form,
        sum(coalesce(passes_accurate, 0)) as passes_accurate_sum_form,
        sum(coalesce(passes_total, 0)) as passes_total_sum_form,
        sum(coalesce(goalkeeper_saves, 0)) as goalkeeper_saves_sum_form
    from form_window_matches
    group by upcoming_fixture_sk, team_sk
)

select
    fixture_sk,
    team_sk,
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
    coalesce(
        safe_divide(points_won_sum_form, nullif(3 * form_games_played, 0)),
        0
    ) as points_capture_recent,
    coalesce(
        safe_divide(goals_for_sum_form, nullif(form_games_played, 0)),
        0
    ) as goals_per_match_recent,
    coalesce(
        safe_divide(goals_against_sum_form, nullif(form_games_played, 0)),
        0
    ) as goals_against_per_match_recent,
    coalesce(
        safe_divide(total_shots_sum_form, nullif(form_games_played, 0)),
        0
    ) as shots_per_match_recent,
    coalesce(
        safe_divide(
            total_shots_sum_form,
            nullif(total_shots_sum_form + opponent_total_shots_sum_form, 0)
        ),
        0
    ) as shot_share_recent,
    coalesce(
        safe_divide(shots_inside_box_sum_form, nullif(total_shots_sum_form, 0)),
        0
    ) as danger_zone_ratio_recent,
    coalesce(
        safe_divide(shots_on_goal_sum_form, nullif(total_shots_sum_form, 0)),
        0
    ) as shot_accuracy_recent,
    coalesce(
        safe_divide(goals_for_sum_form, nullif(shots_on_goal_sum_form, 0)),
        0
    ) as finishing_efficiency_recent,
    coalesce(
        safe_divide(passes_accurate_sum_form, nullif(passes_total_sum_form, 0)),
        0
    ) as pass_accuracy_recent,
    coalesce(
        safe_divide(passes_total_sum_form, nullif(form_games_played, 0)),
        0
    ) as passes_per_match_recent,
    coalesce(
        safe_divide(corner_kicks_sum_form, nullif(form_games_played, 0)),
        0
    ) as corner_kicks_per_match_recent,
    coalesce(
        safe_divide(opponent_corner_kicks_sum_form, nullif(form_games_played, 0)),
        0
    ) as corners_conceded_per_match_recent,
    coalesce(
        safe_divide(
            goalkeeper_saves_sum_form,
            nullif(goalkeeper_saves_sum_form + goals_against_sum_form, 0)
        ),
        0
    ) as save_ratio_recent
from aggregated_form
