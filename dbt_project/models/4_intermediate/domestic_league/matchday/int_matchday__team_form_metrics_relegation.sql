{{ config(materialized='table') }}

{#
  Per (relegation fixture_sk, team_sk) rolling last-five completed legs before kickoff.
  Domestic legs use form_league_code (BL1 or BL2). Completed BL1 play-off legs also count for
  both teams (API files the tie under BL1). Grain: (fixture_sk, team_sk).
#}

with import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

import_int_matchday__relegation_upcoming_fixtures as (
    select * from {{ ref('int_matchday__relegation_upcoming_fixtures') }}
),

import_int_matchday__relegation_team_form_league as (
    select * from {{ ref('int_matchday__relegation_team_form_league') }}
),

team_fixture_context as (
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.home_team_sk as team_sk
    from import_int_matchday__relegation_upcoming_fixtures as um
    union all
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.away_team_sk as team_sk
    from import_int_matchday__relegation_upcoming_fixtures as um
),

team_form_league as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        tfc.league_code,
        tfc.season_api_year,
        tfc.upcoming_kickoff_datetime,
        tfc.upcoming_round_order,
        rfl.form_league_code
    from team_fixture_context as tfc
    inner join import_int_matchday__relegation_team_form_league as rfl
        on
            tfc.upcoming_fixture_sk = rfl.fixture_sk
            and tfc.team_sk = rfl.team_sk
),

current_counts as (
    select
        tfl.upcoming_fixture_sk,
        tfl.team_sk,
        count(*) as n_current_legs_before
    from team_form_league as tfl
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tfl.team_sk = fwo.team_sk
            and tfl.season_api_year = fwo.season_api_year
            and (
                (
                    tfl.form_league_code = fwo.league_code
                )
                or (
                    fwo.league_code = 'BL1'
                    and fwo.round_name in {{ bl1_relegation_round_names_in_clause() }}
                )
            )
            and (
                tfl.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    tfl.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and tfl.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
    group by tfl.upcoming_fixture_sk, tfl.team_sk
),

form_season as (
    select
        tfl.upcoming_fixture_sk,
        tfl.team_sk,
        tfl.league_code,
        tfl.form_league_code,
        tfl.season_api_year,
        tfl.upcoming_kickoff_datetime,
        tfl.upcoming_round_order,
        coalesce(cnt.n_current_legs_before, 0) > 0 as use_five_game_cap,
        case
            when coalesce(cnt.n_current_legs_before, 0) > 0 then tfl.season_api_year
            else tfl.season_api_year - 1
        end as form_season_api_year
    from team_form_league as tfl
    left join current_counts as cnt
        on
            tfl.upcoming_fixture_sk = cnt.upcoming_fixture_sk
            and tfl.team_sk = cnt.team_sk
),

ranked as (
    select
        tsc.upcoming_fixture_sk,
        tsc.team_sk,
        tsc.league_code,
        tsc.form_league_code,
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
        tsc.use_five_game_cap as form_window_five_capped,
        row_number() over (
            partition by tsc.upcoming_fixture_sk, tsc.team_sk
            order by fwo.kickoff_datetime desc, fwo.fixture_sk desc
        ) as game_rn
    from form_season as tsc
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tsc.team_sk = fwo.team_sk
            and tsc.form_season_api_year = fwo.season_api_year
            and (
                (
                    tsc.form_league_code = fwo.league_code
                )
                or (
                    fwo.league_code = 'BL1'
                    and fwo.round_name in {{ bl1_relegation_round_names_in_clause() }}
                )
            )
            and (
                tsc.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    tsc.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and tsc.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
),

form_window_matches as (
    select
        upcoming_fixture_sk,
        team_sk,
        league_code,
        form_league_code,
        fixture_sk,
        kickoff_datetime,
        round_name,
        round_order,
        goals_for,
        goals_against,
        result,
        shots_on_goal,
        shots_total,
        shots_inside_box,
        corner_kicks,
        passes_total,
        passes_accurate,
        goalkeeper_saves,
        opponent_total_shots,
        opponent_corner_kicks,
        form_season_api_year,
        form_window_five_capped
    from ranked
    where not form_window_five_capped or game_rn <= 5
),

form_window_matches_dedup as (
    select * except (leg_dedup_rn)
    from (
        select
            *,
            row_number() over (
                partition by upcoming_fixture_sk, team_sk, fixture_sk
                order by kickoff_datetime desc, fixture_sk desc
            ) as leg_dedup_rn
        from form_window_matches
    )
    where leg_dedup_rn = 1
),

aggregated_form as (
    select
        upcoming_fixture_sk as fixture_sk,
        team_sk,
        any_value(form_league_code) as form_league_code,
        any_value(form_season_api_year) as form_season_api_year,
        max(form_window_five_capped) as form_window_five_capped,
        count(distinct fixture_sk) as form_games_played,
        count(distinct round_name) as form_matchdays_used,
        count(distinct case when shots_on_goal is not null then fixture_sk end) as stat_coverage_form_games,
        sum(
            case upper(trim(result))
                when 'W' then 3
                when 'D' then 1
                else 0
            end
        ) as points_won_sum_form,
        sum(goals_for) as goals_for_sum_form,
        sum(goals_against) as goals_against_sum_form,
        sum(shots_total) as total_shots_sum_form,
        sum(opponent_total_shots) as opponent_total_shots_sum_form,
        sum(shots_inside_box) as shots_inside_box_sum_form,
        sum(shots_on_goal) as shots_on_goal_sum_form,
        sum(corner_kicks) as corner_kicks_sum_form,
        sum(opponent_corner_kicks) as opponent_corner_kicks_sum_form,
        sum(passes_accurate) as passes_accurate_sum_form,
        sum(passes_total) as passes_total_sum_form,
        sum(goalkeeper_saves) as goalkeeper_saves_sum_form
    from form_window_matches_dedup
    group by upcoming_fixture_sk, team_sk
),

form_context as (
    select
        upcoming_fixture_sk as fixture_sk,
        team_sk,
        form_league_code,
        form_season_api_year,
        use_five_game_cap as form_window_five_capped
    from form_season
),

form_metrics as (
    select
        fc.fixture_sk,
        fc.team_sk,
        fc.form_league_code,
        fc.form_season_api_year,
        fc.form_window_five_capped,
        af.points_won_sum_form,
        af.goals_for_sum_form,
        af.goals_against_sum_form,
        af.total_shots_sum_form,
        af.opponent_total_shots_sum_form,
        af.shots_inside_box_sum_form,
        af.shots_on_goal_sum_form,
        af.corner_kicks_sum_form,
        af.opponent_corner_kicks_sum_form,
        af.passes_accurate_sum_form,
        af.passes_total_sum_form,
        af.goalkeeper_saves_sum_form,
        coalesce(af.form_games_played, 0) as form_games_played,
        coalesce(af.form_matchdays_used, 0) as form_matchdays_used,
        coalesce(af.stat_coverage_form_games, 0) as stat_coverage_form_games
    from form_context as fc
    left join aggregated_form as af
        on
            fc.fixture_sk = af.fixture_sk
            and fc.team_sk = af.team_sk
)

select
    fixture_sk,
    team_sk,
    form_league_code,
    form_season_api_year,
    form_window_five_capped,
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
    safe_divide(points_won_sum_form, 3 * form_games_played) as points_capture_recent,
    safe_divide(goals_for_sum_form, form_games_played) as goals_per_match_recent,
    safe_divide(goals_against_sum_form, form_games_played) as goals_against_per_match_recent,
    safe_divide(total_shots_sum_form, form_games_played) as shots_per_match_recent,
    safe_divide(
        total_shots_sum_form,
        nullif(total_shots_sum_form + opponent_total_shots_sum_form, 0)
    ) as shot_share_recent,
    safe_divide(shots_inside_box_sum_form, total_shots_sum_form) as danger_zone_ratio_recent,
    safe_divide(shots_on_goal_sum_form, total_shots_sum_form) as shot_accuracy_recent,
    case
        when shots_on_goal_sum_form is null or shots_on_goal_sum_form = 0 then null
        when goals_for_sum_form > shots_on_goal_sum_form then null
        else safe_divide(goals_for_sum_form, shots_on_goal_sum_form)
    end as finishing_efficiency_recent,
    safe_divide(passes_accurate_sum_form, passes_total_sum_form) as pass_accuracy_recent,
    safe_divide(passes_total_sum_form, form_games_played) as passes_per_match_recent,
    safe_divide(corner_kicks_sum_form, form_games_played) as corner_kicks_per_match_recent,
    safe_divide(opponent_corner_kicks_sum_form, form_games_played) as corners_conceded_per_match_recent,
    safe_divide(
        goalkeeper_saves_sum_form,
        nullif(goalkeeper_saves_sum_form + goals_against_sum_form, 0)
    ) as save_ratio_recent
from form_metrics
