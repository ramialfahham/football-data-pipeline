{{ config(materialized='view') }}

with mart_fixture_results as (
    select * from {{ ref('mart_fixture_results') }}
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
        league_code = 'D1'
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
        order by fixture_date asc, kickoff_datetime asc
    ) = 1
),

upcoming_matchday as (
    select uc.*
    from upcoming_candidates as uc
    inner join next_round as nr
        on
            uc.league_code = nr.league_code
            and uc.season_api_year = nr.season_api_year
            and uc.round_name = nr.round_name
),

finished_legs as (
    select
        f.fixture_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
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
        fl.goals_for,
        fl.goals_against,
        fl.result,
        stats.shots_on_goal,
        stats.shots_outside_box,
        stats.offsides
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
        fts.goals_for,
        fts.goals_against,
        fts.result,
        fts.shots_on_goal,
        fts.shots_outside_box,
        fts.offsides,
        opp.shots_on_goal as opponent_shots_on_goal
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
        um.home_team_sk as team_sk
    from upcoming_matchday as um
    union all
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.away_team_sk as team_sk
    from upcoming_matchday as um
),

ranked_recent as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        fwo.fixture_sk,
        fwo.kickoff_datetime,
        fwo.goals_for,
        fwo.goals_against,
        fwo.result,
        fwo.shots_on_goal,
        fwo.shots_outside_box,
        fwo.offsides,
        fwo.opponent_shots_on_goal,
        row_number() over (
            partition by tfc.upcoming_fixture_sk, tfc.team_sk
            order by fwo.kickoff_datetime desc, fwo.fixture_sk desc
        ) as recent_match_rank
    from team_fixture_context as tfc
    inner join finished_with_opponent as fwo
        on
            tfc.team_sk = fwo.team_sk
            and tfc.league_code = fwo.league_code
            and tfc.season_api_year = fwo.season_api_year
            and tfc.upcoming_kickoff_datetime > fwo.kickoff_datetime
),

aggregated_recent as (
    select
        upcoming_fixture_sk as fixture_sk,
        team_sk,
        countif(recent_match_rank <= 5) as played_last5,
        countif(recent_match_rank <= 10) as played_last10,
        countif(recent_match_rank <= 5 and shots_on_goal is not null) as stat_coverage_last5,
        countif(recent_match_rank <= 10 and shots_on_goal is not null) as stat_coverage_last10,
        avg(if(recent_match_rank <= 5, cast(result = 'W' as int64), null)) as win_rate_last5_raw,
        avg(if(recent_match_rank <= 10, cast(result = 'W' as int64), null)) as win_rate_last10_raw,
        avg(if(recent_match_rank <= 5, goals_for, null)) as goals_per_match_last5_raw,
        avg(if(recent_match_rank <= 10, goals_for, null)) as goals_per_match_last10_raw,
        avg(if(recent_match_rank <= 5, shots_on_goal, null)) as shots_on_target_last5_raw,
        avg(if(recent_match_rank <= 10, shots_on_goal, null)) as shots_on_target_last10_raw,
        avg(if(recent_match_rank <= 5, coalesce(shots_on_goal, 0) - coalesce(opponent_shots_on_goal, 0), null)) as shot_balance_last5_raw,
        avg(if(recent_match_rank <= 10, coalesce(shots_on_goal, 0) - coalesce(opponent_shots_on_goal, 0), null)) as shot_balance_last10_raw,
        safe_divide(sum(if(recent_match_rank <= 5, goals_for, null)), nullif(sum(if(recent_match_rank <= 5, shots_on_goal, null)), 0)) as shot_quality_conversion_last5_raw,
        safe_divide(sum(if(recent_match_rank <= 10, goals_for, null)), nullif(sum(if(recent_match_rank <= 10, shots_on_goal, null)), 0)) as shot_quality_conversion_last10_raw,
        avg(if(recent_match_rank <= 5, coalesce(opponent_shots_on_goal, 0), null)) as shots_allowed_last5_raw,
        avg(if(recent_match_rank <= 10, coalesce(opponent_shots_on_goal, 0), null)) as shots_allowed_last10_raw,
        avg(if(recent_match_rank <= 5, coalesce(shots_outside_box, 0) + coalesce(offsides, 0), null)) as transition_threat_last5_raw,
        avg(if(recent_match_rank <= 10, coalesce(shots_outside_box, 0) + coalesce(offsides, 0), null)) as transition_threat_last10_raw
    from ranked_recent
    where recent_match_rank <= 10
    group by upcoming_fixture_sk, team_sk
),

team_recent_metrics as (
    select
        fixture_sk,
        team_sk,
        played_last5,
        played_last10,
        stat_coverage_last5,
        stat_coverage_last10,
        case
            when stat_coverage_last5 >= 3 then 'LAST5'
            when stat_coverage_last10 >= 3 then 'LAST10'
            else 'LOW'
        end as coverage_bucket,
        if(stat_coverage_last5 >= 3, win_rate_last5_raw, win_rate_last10_raw) as win_rate_recent,
        if(stat_coverage_last5 >= 3, goals_per_match_last5_raw, goals_per_match_last10_raw) as goals_per_match_recent,
        if(stat_coverage_last5 >= 3, shots_on_target_last5_raw, shots_on_target_last10_raw) as shots_on_target_recent,
        if(stat_coverage_last5 >= 3, shot_balance_last5_raw, shot_balance_last10_raw) as shot_balance_recent,
        if(stat_coverage_last5 >= 3, shot_quality_conversion_last5_raw, shot_quality_conversion_last10_raw) as shot_quality_conversion_recent,
        if(stat_coverage_last5 >= 3, shots_allowed_last5_raw, shots_allowed_last10_raw) as shots_allowed_recent,
        if(stat_coverage_last5 >= 3, transition_threat_last5_raw, transition_threat_last10_raw) as transition_threat_recent
    from aggregated_recent
),

home_metrics as (
    select
        fixture_sk,
        team_sk as home_team_sk,
        played_last5 as home_recent_matches_played_last5,
        stat_coverage_last5 as home_stat_coverage_last5,
        coverage_bucket as home_coverage_bucket,
        win_rate_recent as home_win_rate_recent,
        goals_per_match_recent as home_goals_per_match_recent,
        shots_on_target_recent as home_shots_on_target_per_match_recent,
        shot_balance_recent as home_shot_balance_recent,
        shot_quality_conversion_recent as home_shot_quality_conversion_recent,
        shots_allowed_recent as home_shots_allowed_per_match_recent,
        transition_threat_recent as home_transition_threat_recent
    from team_recent_metrics
),

away_metrics as (
    select
        fixture_sk,
        team_sk as away_team_sk,
        played_last5 as away_recent_matches_played_last5,
        stat_coverage_last5 as away_stat_coverage_last5,
        coverage_bucket as away_coverage_bucket,
        win_rate_recent as away_win_rate_recent,
        goals_per_match_recent as away_goals_per_match_recent,
        shots_on_target_recent as away_shots_on_target_per_match_recent,
        shot_balance_recent as away_shot_balance_recent,
        shot_quality_conversion_recent as away_shot_quality_conversion_recent,
        shots_allowed_recent as away_shots_allowed_per_match_recent,
        transition_threat_recent as away_transition_threat_recent
    from team_recent_metrics
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
        um.league_name,
        um.home_team_sk,
        um.home_team_name,
        um.away_team_sk,
        um.away_team_name,
        hm.home_recent_matches_played_last5,
        hm.home_stat_coverage_last5,
        hm.home_coverage_bucket,
        hm.home_win_rate_recent,
        hm.home_goals_per_match_recent,
        hm.home_shots_on_target_per_match_recent,
        hm.home_shot_balance_recent,
        hm.home_shot_quality_conversion_recent,
        hm.home_shots_allowed_per_match_recent,
        hm.home_transition_threat_recent,
        am.away_recent_matches_played_last5,
        am.away_stat_coverage_last5,
        am.away_coverage_bucket,
        am.away_win_rate_recent,
        am.away_goals_per_match_recent,
        am.away_shots_on_target_per_match_recent,
        am.away_shot_balance_recent,
        am.away_shot_quality_conversion_recent,
        am.away_shots_allowed_per_match_recent,
        am.away_transition_threat_recent,
        coalesce(hm.home_shot_balance_recent, 0) - coalesce(am.away_shot_balance_recent, 0) as shot_balance_edge_home,
        coalesce(hm.home_shot_quality_conversion_recent, 0) - coalesce(am.away_shot_quality_conversion_recent, 0) as shot_quality_conversion_edge_home,
        coalesce(am.away_shots_allowed_per_match_recent, 0) - coalesce(hm.home_shots_allowed_per_match_recent, 0) as defensive_suppression_edge_home,
        coalesce(hm.home_transition_threat_recent, 0) - coalesce(am.away_transition_threat_recent, 0) as transition_threat_edge_home,
        format_date('%A', um.fixture_date) as kickoff_weekday_utc,
        case
            when coalesce(hm.home_shot_balance_recent, 0) - coalesce(am.away_shot_balance_recent, 0) >= 0.5 then 'HOME_CHANCE_EDGE'
            when coalesce(hm.home_shot_balance_recent, 0) - coalesce(am.away_shot_balance_recent, 0) <= -0.5 then 'AWAY_CHANCE_EDGE'
            else 'BALANCED'
        end as clash_verdict
    from upcoming_matchday as um
    left join home_metrics as hm
        on
            um.fixture_sk = hm.fixture_sk
            and um.home_team_sk = hm.home_team_sk
    left join away_metrics as am
        on
            um.fixture_sk = am.fixture_sk
            and um.away_team_sk = am.away_team_sk
)

select *
from final
order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
