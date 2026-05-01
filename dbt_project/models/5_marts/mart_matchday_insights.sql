{{ config(materialized='view') }}

with mart_fixture_results as (
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
    from {{ ref('mart_fixture_results') }}
),

mart_team_season as (
    select
        team_sk,
        season_sk,
        latest_rank
    from {{ ref('mart_team_season') }}
),

fct_fixture as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        home_team_sk,
        away_team_sk,
        goals_home,
        goals_away,
        status_short
    from {{ ref('fct_fixture') }}
),

fct_fixture_team_stats as (
    select
        fixture_sk,
        team_sk,
        shots_on_goal,
        shots_total,
        shots_inside_box,
        corner_kicks,
        passes_total,
        passes_accurate,
        goalkeeper_saves
    from {{ ref('fct_fixture_team_stats') }}
),

app_visible_competitions as (
    {% set visible_competitions = var('app_visible_competitions', []) %}
    {% if visible_competitions | length == 0 %}
    select
        case
            when league_code = 'D1' then 'BL1'
            else league_code
        end as league_code,
        cast('1900-01-01' as date) as visible_from,
        cast(null as date) as visible_until
    from (
        select distinct league_code
        from mart_fixture_results
        where league_code is not null
    )
    {% else %}
    {% for comp in visible_competitions %}
    select
        '{{ comp["league_code"] }}' as league_code,
        cast('{{ comp["visible_from"] }}' as date) as visible_from,
        cast(
            {% if comp["visible_until"] %}'{{ comp["visible_until"] }}'{% else %}null{% endif %}
            as date
        ) as visible_until
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
    {% endif %}
),

upcoming_candidates as (
    select
        mfr.fixture_sk,
        mfr.fixture_api_id,
        mfr.league_sk,
        mfr.season_sk,
        mfr.home_team_sk,
        mfr.away_team_sk,
        case
            when mfr.league_code = 'D1' then 'BL1'
            else mfr.league_code
        end as league_code,
        mfr.season_api_year,
        mfr.fixture_date,
        mfr.kickoff_datetime,
        mfr.round_name,
        mfr.home_team_name,
        mfr.away_team_name,
        mfr.league_name,
        mfr.status_short
    from mart_fixture_results as mfr
    inner join app_visible_competitions as avc
        on
            (
                case
                    when mfr.league_code = 'D1' then 'BL1'
                    else mfr.league_code
                end
            ) = avc.league_code
    where
        mfr.status_short in ('NS', 'TBD')
        and mfr.fixture_date >= current_date()
        and mfr.fixture_date >= avc.visible_from
        and (avc.visible_until is null or mfr.fixture_date <= avc.visible_until)
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
        case
            when f.league_code = 'D1' then 'BL1'
            else f.league_code
        end as league_code,
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
        case
            when f.league_code = 'D1' then 'BL1'
            else f.league_code
        end as league_code,
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

past_team_matches as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
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
        dense_rank() over (
            partition by tfc.upcoming_fixture_sk, tfc.team_sk
            order by fwo.round_order desc nulls last, fwo.kickoff_datetime desc
        ) as recent_matchday_rank
    from team_fixture_context as tfc
    inner join finished_with_opponent as fwo
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
),

form_window_matches as (
    select
        upcoming_fixture_sk,
        team_sk,
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
        recent_matchday_rank
    from past_team_matches
    where recent_matchday_rank <= 5
),

aggregated_form as (
    select
        upcoming_fixture_sk as fixture_sk,
        team_sk,
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
        form_games_played,
        form_matchdays_used,
        stat_coverage_form_games,
        points_won_sum_form,
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
        form_games_played as home_form_games_played,
        form_matchdays_used as home_form_matchdays_used,
        stat_coverage_form_games as home_stat_coverage_form_games,
        points_won_sum_form as home_points_won_sum_form,
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
        form_games_played as away_form_games_played,
        form_matchdays_used as away_form_matchdays_used,
        stat_coverage_form_games as away_stat_coverage_form_games,
        points_won_sum_form as away_points_won_sum_form,
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
        hf.home_form_games_played,
        hf.home_form_matchdays_used,
        hf.home_stat_coverage_form_games,
        hf.home_points_won_sum_form,
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
        af.away_form_games_played,
        af.away_form_matchdays_used,
        af.away_stat_coverage_form_games,
        af.away_points_won_sum_form,
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
        um.league_name
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

select
    fixture_sk,
    fixture_api_id,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    fixture_date,
    kickoff_datetime,
    round_name,
    upcoming_round_order,
    home_team_sk,
    home_team_name,
    away_team_sk,
    away_team_name,
    upcoming_matchday_fixture_count,
    home_league_rank,
    away_league_rank,
    home_form_games_played,
    home_form_matchdays_used,
    home_stat_coverage_form_games,
    home_points_won_sum_form,
    home_points_capture_recent,
    home_goals_per_match_recent,
    home_goals_against_per_match_recent,
    home_shots_per_match_recent,
    home_shot_share_recent,
    home_danger_zone_ratio_recent,
    home_shot_accuracy_recent,
    home_finishing_efficiency_recent,
    home_pass_accuracy_recent,
    home_passes_per_match_recent,
    home_corner_kicks_per_match_recent,
    home_corners_conceded_per_match_recent,
    home_save_ratio_recent,
    away_form_games_played,
    away_form_matchdays_used,
    away_stat_coverage_form_games,
    away_points_won_sum_form,
    away_points_capture_recent,
    away_goals_per_match_recent,
    away_goals_against_per_match_recent,
    away_shots_per_match_recent,
    away_shot_share_recent,
    away_danger_zone_ratio_recent,
    away_shot_accuracy_recent,
    away_finishing_efficiency_recent,
    away_pass_accuracy_recent,
    away_passes_per_match_recent,
    away_corner_kicks_per_match_recent,
    away_corners_conceded_per_match_recent,
    away_save_ratio_recent,
    league_name
from final
order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
