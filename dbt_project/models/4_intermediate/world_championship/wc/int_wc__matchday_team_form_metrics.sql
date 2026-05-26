{{ config(materialized='table') }}

{#
  Per (upcoming WC fixture_sk, team_sk) form aggregates. Grain: (fixture_sk, team_sk).

  Phase rules:
    - Group Stage round 1: form from all finished supporting qualifier legs for that team.
    - From Group Stage round 2 onward (including knockout rounds): form from all finished
      WC tournament legs before the reference fixture kickoff (cumulative, no five-game cap).

  Optional stats remain nullable; rates are null when undefined.
#}

with import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

import_int_matchday__upcoming_round_fixtures as (
    select * from {{ ref('int_matchday__upcoming_round_fixtures') }}
    where
        league_code = 'WC'
        and status_short = 'NS'
        and home_team_sk is not null
        and away_team_sk is not null
),

supporting_leagues as (
    select
        parent_league_code,
        supporting_league_code,
        qualifier_season_api_year
    from {{ ref('wc_supporting_league_codes') }}
    where parent_league_code = 'WC'
),

team_fixture_context as (
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.season_api_year,
        um.round_name as upcoming_round_name,
        um.upcoming_round_order,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.home_team_sk as team_sk
    from import_int_matchday__upcoming_round_fixtures as um
    union all
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.season_api_year,
        um.round_name as upcoming_round_name,
        um.upcoming_round_order,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.away_team_sk as team_sk
    from import_int_matchday__upcoming_round_fixtures as um
),

form_phase as (
    select
        upcoming_fixture_sk,
        season_api_year,
        upcoming_kickoff_datetime,
        team_sk,
        coalesce(upcoming_round_order, -1) != 1
        or not regexp_contains(lower(coalesce(upcoming_round_name, '')), r'group') as is_tournament_form
    from team_fixture_context
),

qualifier_window as (
    select
        fp.upcoming_fixture_sk,
        fp.team_sk,
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
        fwo.season_api_year as form_season_api_year,
        false as is_tournament_form
    from form_phase as fp
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            fp.team_sk = fwo.team_sk
            and (
                fp.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    fp.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and fp.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
    inner join supporting_leagues as sl
        on
            fwo.league_code = sl.supporting_league_code
            and fwo.season_api_year = sl.qualifier_season_api_year
    where not fp.is_tournament_form
),

tournament_window as (
    select
        fp.upcoming_fixture_sk,
        fp.team_sk,
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
        fwo.season_api_year as form_season_api_year,
        true as is_tournament_form
    from form_phase as fp
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            fp.team_sk = fwo.team_sk
            and fwo.league_code = 'WC'
            and fp.season_api_year = fwo.season_api_year
            and (
                fp.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    fp.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and fp.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
    where fp.is_tournament_form
),

form_window_matches as (
    select * from qualifier_window
    union all
    select * from tournament_window
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
        max(form_season_api_year) as form_season_api_year,
        max(is_tournament_form) as is_tournament_form,
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
        season_api_year as form_season_api_year,
        is_tournament_form
    from form_phase
),

form_metrics as (
    select
        fc.fixture_sk,
        fc.team_sk,
        fc.is_tournament_form,
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
        coalesce(af.form_season_api_year, fc.form_season_api_year) as form_season_api_year,
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
    form_season_api_year,
    is_tournament_form,
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
