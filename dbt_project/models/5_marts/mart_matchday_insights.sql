{{ config(materialized='view') }}

with mart_fixture_results as (
    select * from {{ ref('mart_fixture_results') }}
),

mart_team_season as (
    select * from {{ ref('mart_team_season') }}
),

fct_fixture as (
    select * from {{ ref('fct_fixture') }}
),

fct_fixture_team_stats as (
    select * from {{ ref('fct_fixture_team_stats') }}
),

upcoming_candidates as (
    select
        fixture_sk,
        fixture_api_id,
        league_sk,
        season_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year,
        fixture_date,
        kickoff_datetime,
        round_name,
        home_team_name,
        away_team_name,
        league_name,
        status_short
    from mart_fixture_results
    where
        league_code = 'BL1'
        and status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

next_round as (
    select
        league_code,
        season_api_year,
        round_name
    from upcoming_candidates
    qualify row_number() over (
        partition by league_code, season_api_year
        order by fixture_date asc, kickoff_datetime asc
    ) = 1
),

upcoming_matchday as (
    select
        uc.*,
        safe_cast(regexp_extract(uc.round_name, r'(\d+)$') as int64) as upcoming_round_order
    from upcoming_candidates as uc
    inner join next_round as nr
        on
            uc.league_code = nr.league_code
            and uc.season_api_year = nr.season_api_year
            and uc.round_name = nr.round_name
),

matchday_fixture_count as (
    select
        league_code,
        season_api_year,
        round_name,
        count(*) as upcoming_matchday_fixture_count
    from upcoming_matchday
    group by league_code, season_api_year, round_name
),

finished_legs as (
    select
        f.fixture_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.round_name,
        safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
        f.home_team_sk as team_sk,
        f.away_team_sk as opponent_team_sk,
        f.goals_home as goals_for,
        f.goals_away as goals_against,
        case
            when f.goals_home > f.goals_away then 'W'
            when f.goals_home < f.goals_away then 'L'
            else 'D'
        end as result
    from fct_fixture as f
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and f.goals_home is not null
        and f.goals_away is not null
    union all
    select
        f.fixture_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.round_name,
        safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
        f.away_team_sk as team_sk,
        f.home_team_sk as opponent_team_sk,
        f.goals_away as goals_for,
        f.goals_home as goals_against,
        case
            when f.goals_away > f.goals_home then 'W'
            when f.goals_away < f.goals_home then 'L'
            else 'D'
        end as result
    from fct_fixture as f
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and f.goals_home is not null
        and f.goals_away is not null
),

finished_team_stats as (
    select
        fl.fixture_sk,
        fl.team_sk,
        fl.opponent_team_sk,
        fl.league_code,
        fl.season_api_year,
        fl.kickoff_datetime,
        fl.round_name,
        fl.round_order,
        fl.goals_for,
        fl.goals_against,
        fl.result,
        stats.shots_on_goal,
        stats.shots_total,
        stats.shots_inside_box,
        stats.corner_kicks,
        stats.passes_total,
        stats.passes_accurate,
        stats.goalkeeper_saves
    from finished_legs as fl
    left join fct_fixture_team_stats as stats
        on
            fl.fixture_sk = stats.fixture_sk
            and fl.team_sk = stats.team_sk
),

finished_with_opponent as (
    select
        fts.fixture_sk,
        fts.team_sk,
        fts.league_code,
        fts.season_api_year,
        fts.kickoff_datetime,
        fts.round_name,
        fts.round_order,
        fts.goals_for,
        fts.goals_against,
        fts.result,
        fts.shots_on_goal,
        fts.shots_total,
        fts.shots_inside_box,
        fts.corner_kicks,
        fts.passes_total,
        fts.passes_accurate,
        fts.goalkeeper_saves,
        opp.shots_total as opponent_total_shots,
        opp.corner_kicks as opponent_corner_kicks
    from finished_team_stats as fts
    left join finished_team_stats as opp
        on
            fts.fixture_sk = opp.fixture_sk
            and fts.team_sk != opp.team_sk
),

team_fixture_context as (
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.home_team_sk as team_sk
    from upcoming_matchday as um
    union all
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.away_team_sk as team_sk
    from upcoming_matchday as um
),

current_season_game_counts as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        count(fwo.fixture_sk) as completed_games_in_current_season
    from team_fixture_context as tfc
    left join finished_with_opponent as fwo
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
    inner join finished_with_opponent as fwo
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
),

team_form_metrics as (
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
),

home_form as (
    select
        fixture_sk,
        team_sk as home_team_sk,
        form_season_api_year as home_form_season_api_year,
        form_games_played as home_form_games_played,
        form_matchdays_used as home_form_matchdays_used,
        stat_coverage_form_games as home_stat_coverage_form_games,
        points_won_sum_form as home_points_won_sum_form,
        goals_for_sum_form as home_goals_for_sum_form,
        goals_against_sum_form as home_goals_against_sum_form,
        total_shots_sum_form as home_total_shots_sum_form,
        opponent_total_shots_sum_form as home_opponent_total_shots_sum_form,
        shots_inside_box_sum_form as home_shots_inside_box_sum_form,
        shots_on_goal_sum_form as home_shots_on_goal_sum_form,
        corner_kicks_sum_form as home_corner_kicks_sum_form,
        opponent_corner_kicks_sum_form as home_opponent_corner_kicks_sum_form,
        passes_accurate_sum_form as home_passes_accurate_sum_form,
        passes_total_sum_form as home_passes_total_sum_form,
        goalkeeper_saves_sum_form as home_goalkeeper_saves_sum_form,
        points_capture_recent as home_points_capture_recent,
        goals_per_match_recent as home_goals_per_match_recent,
        goals_against_per_match_recent as home_goals_against_per_match_recent,
        shots_per_match_recent as home_shots_per_match_recent,
        shot_share_recent as home_shot_share_recent,
        danger_zone_ratio_recent as home_danger_zone_ratio_recent,
        shot_accuracy_recent as home_shot_accuracy_recent,
        finishing_efficiency_recent as home_finishing_efficiency_recent,
        pass_accuracy_recent as home_pass_accuracy_recent,
        passes_per_match_recent as home_passes_per_match_recent,
        corner_kicks_per_match_recent as home_corner_kicks_per_match_recent,
        corners_conceded_per_match_recent as home_corners_conceded_per_match_recent,
        save_ratio_recent as home_save_ratio_recent
    from team_form_metrics
),

away_form as (
    select
        fixture_sk,
        team_sk as away_team_sk,
        form_season_api_year as away_form_season_api_year,
        form_games_played as away_form_games_played,
        form_matchdays_used as away_form_matchdays_used,
        stat_coverage_form_games as away_stat_coverage_form_games,
        points_won_sum_form as away_points_won_sum_form,
        goals_for_sum_form as away_goals_for_sum_form,
        goals_against_sum_form as away_goals_against_sum_form,
        total_shots_sum_form as away_total_shots_sum_form,
        opponent_total_shots_sum_form as away_opponent_total_shots_sum_form,
        shots_inside_box_sum_form as away_shots_inside_box_sum_form,
        shots_on_goal_sum_form as away_shots_on_goal_sum_form,
        corner_kicks_sum_form as away_corner_kicks_sum_form,
        opponent_corner_kicks_sum_form as away_opponent_corner_kicks_sum_form,
        passes_accurate_sum_form as away_passes_accurate_sum_form,
        passes_total_sum_form as away_passes_total_sum_form,
        goalkeeper_saves_sum_form as away_goalkeeper_saves_sum_form,
        points_capture_recent as away_points_capture_recent,
        goals_per_match_recent as away_goals_per_match_recent,
        goals_against_per_match_recent as away_goals_against_per_match_recent,
        shots_per_match_recent as away_shots_per_match_recent,
        shot_share_recent as away_shot_share_recent,
        danger_zone_ratio_recent as away_danger_zone_ratio_recent,
        shot_accuracy_recent as away_shot_accuracy_recent,
        finishing_efficiency_recent as away_finishing_efficiency_recent,
        pass_accuracy_recent as away_pass_accuracy_recent,
        passes_per_match_recent as away_passes_per_match_recent,
        corner_kicks_per_match_recent as away_corner_kicks_per_match_recent,
        corners_conceded_per_match_recent as away_corners_conceded_per_match_recent,
        save_ratio_recent as away_save_ratio_recent
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
        mfc.upcoming_matchday_fixture_count,
        home_ts.latest_rank as home_league_rank,
        away_ts.latest_rank as away_league_rank,
        home_ts.standings_group_description as home_standings_group_description,
        away_ts.standings_group_description as away_standings_group_description,
        hf.home_form_season_api_year,
        hf.home_form_games_played,
        hf.home_form_matchdays_used,
        hf.home_stat_coverage_form_games,
        hf.home_points_won_sum_form,
        hf.home_goals_for_sum_form,
        hf.home_goals_against_sum_form,
        hf.home_total_shots_sum_form,
        hf.home_opponent_total_shots_sum_form,
        hf.home_shots_inside_box_sum_form,
        hf.home_shots_on_goal_sum_form,
        hf.home_corner_kicks_sum_form,
        hf.home_opponent_corner_kicks_sum_form,
        hf.home_passes_accurate_sum_form,
        hf.home_passes_total_sum_form,
        hf.home_goalkeeper_saves_sum_form,
        hf.home_points_capture_recent,
        hf.home_goals_per_match_recent,
        hf.home_goals_against_per_match_recent,
        hf.home_shots_per_match_recent,
        hf.home_shot_share_recent,
        hf.home_danger_zone_ratio_recent,
        hf.home_shot_accuracy_recent,
        hf.home_finishing_efficiency_recent,
        hf.home_pass_accuracy_recent,
        hf.home_passes_per_match_recent,
        hf.home_corner_kicks_per_match_recent,
        hf.home_corners_conceded_per_match_recent,
        hf.home_save_ratio_recent,
        af.away_form_season_api_year,
        af.away_form_games_played,
        af.away_form_matchdays_used,
        af.away_stat_coverage_form_games,
        af.away_points_won_sum_form,
        af.away_goals_for_sum_form,
        af.away_goals_against_sum_form,
        af.away_total_shots_sum_form,
        af.away_opponent_total_shots_sum_form,
        af.away_shots_inside_box_sum_form,
        af.away_shots_on_goal_sum_form,
        af.away_corner_kicks_sum_form,
        af.away_opponent_corner_kicks_sum_form,
        af.away_passes_accurate_sum_form,
        af.away_passes_total_sum_form,
        af.away_goalkeeper_saves_sum_form,
        af.away_points_capture_recent,
        af.away_goals_per_match_recent,
        af.away_goals_against_per_match_recent,
        af.away_shots_per_match_recent,
        af.away_shot_share_recent,
        af.away_danger_zone_ratio_recent,
        af.away_shot_accuracy_recent,
        af.away_finishing_efficiency_recent,
        af.away_pass_accuracy_recent,
        af.away_passes_per_match_recent,
        af.away_corner_kicks_per_match_recent,
        af.away_corners_conceded_per_match_recent,
        af.away_save_ratio_recent,
        case
            when um.league_code = 'BL1' then 'Bundesliga'
            else um.league_name
        end as league_name
    from upcoming_matchday as um
    inner join matchday_fixture_count as mfc
        on
            um.league_code = mfc.league_code
            and um.season_api_year = mfc.season_api_year
            and um.round_name = mfc.round_name
    left join mart_team_season as home_ts
        on
            um.home_team_sk = home_ts.team_sk
            and um.season_sk = home_ts.season_sk
    left join mart_team_season as away_ts
        on
            um.away_team_sk = away_ts.team_sk
            and um.season_sk = away_ts.season_sk
    left join home_form as hf
        on
            um.fixture_sk = hf.fixture_sk
            and um.home_team_sk = hf.home_team_sk
    left join away_form as af
        on
            um.fixture_sk = af.fixture_sk
            and um.away_team_sk = af.away_team_sk
)

select *
from final
order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
