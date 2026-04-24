{{ config(materialized='view') }}

{#
    Matchday "style clash" surface for upcoming D1 fixtures.
    Grain: one row per fixture for the nearest upcoming round.
#}

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
        f.fixture_date,
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
        f.fixture_date,
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
        fl.fixture_date,
        fl.kickoff_datetime,
        fl.goals_for,
        fl.goals_against,
        fl.result,
        stats.shots_on_goal,
        stats.shots_total,
        stats.shots_outside_box,
        stats.corner_kicks,
        stats.offsides,
        stats.expected_goals
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
        fts.fixture_date,
        fts.kickoff_datetime,
        fts.goals_for,
        fts.goals_against,
        fts.result,
        fts.shots_on_goal,
        fts.shots_total,
        fts.shots_outside_box,
        fts.corner_kicks,
        fts.offsides,
        fts.expected_goals,
        opp.shots_total as opponent_shots_total,
        opp.expected_goals as opponent_expected_goals
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
        fwo.fixture_date,
        fwo.kickoff_datetime,
        fwo.goals_for,
        fwo.goals_against,
        fwo.result,
        fwo.shots_on_goal,
        fwo.shots_total,
        fwo.shots_outside_box,
        fwo.corner_kicks,
        fwo.offsides,
        fwo.expected_goals,
        fwo.opponent_shots_total,
        fwo.opponent_expected_goals,
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

last_five as (
    select *
    from ranked_recent
    where recent_match_rank <= 5
),

team_recent_metrics as (
    select
        upcoming_fixture_sk as fixture_sk,
        team_sk,
        count(*) as recent_matches_played,
        avg(cast(result = 'W' as int64)) as win_rate_last5,
        avg(goals_for) as goals_per_match_last5,
        avg(shots_on_goal) as shots_on_target_per_match_last5,
        avg(expected_goals - coalesce(opponent_expected_goals, 0)) as xg_delta_last5,
        safe_divide(sum(goals_for), nullif(sum(expected_goals), 0))
            as shot_quality_conversion_last5,
        avg(coalesce(opponent_expected_goals, 0)) as xga_per_match_last5,
        avg(coalesce(opponent_shots_total, 0)) as shots_conceded_per_match_last5,
        avg(coalesce(shots_outside_box, 0) + coalesce(offsides, 0))
            as transition_threat_last5,
        avg(coalesce(corner_kicks, 0)) as set_piece_threat_last5
    from last_five
    group by upcoming_fixture_sk, team_sk
),

home_metrics as (
    select
        fixture_sk,
        team_sk as home_team_sk,
        recent_matches_played as home_recent_matches_played,
        win_rate_last5 as home_win_rate_last5,
        goals_per_match_last5 as home_goals_per_match_last5,
        shots_on_target_per_match_last5 as home_shots_on_target_per_match_last5,
        xg_delta_last5 as home_xg_delta_last5,
        shot_quality_conversion_last5 as home_shot_quality_conversion_last5,
        xga_per_match_last5 as home_xga_per_match_last5,
        shots_conceded_per_match_last5 as home_shots_conceded_per_match_last5,
        transition_threat_last5 as home_transition_threat_last5,
        set_piece_threat_last5 as home_set_piece_threat_last5
    from team_recent_metrics
),

away_metrics as (
    select
        fixture_sk,
        team_sk as away_team_sk,
        recent_matches_played as away_recent_matches_played,
        win_rate_last5 as away_win_rate_last5,
        goals_per_match_last5 as away_goals_per_match_last5,
        shots_on_target_per_match_last5 as away_shots_on_target_per_match_last5,
        xg_delta_last5 as away_xg_delta_last5,
        shot_quality_conversion_last5 as away_shot_quality_conversion_last5,
        xga_per_match_last5 as away_xga_per_match_last5,
        shots_conceded_per_match_last5 as away_shots_conceded_per_match_last5,
        transition_threat_last5 as away_transition_threat_last5,
        set_piece_threat_last5 as away_set_piece_threat_last5
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
        hm.home_recent_matches_played,
        hm.home_win_rate_last5,
        hm.home_goals_per_match_last5,
        hm.home_shots_on_target_per_match_last5,
        hm.home_xg_delta_last5,
        hm.home_shot_quality_conversion_last5,
        hm.home_xga_per_match_last5,
        hm.home_shots_conceded_per_match_last5,
        hm.home_transition_threat_last5,
        hm.home_set_piece_threat_last5,
        am.away_recent_matches_played,
        am.away_win_rate_last5,
        am.away_goals_per_match_last5,
        am.away_shots_on_target_per_match_last5,
        am.away_xg_delta_last5,
        am.away_shot_quality_conversion_last5,
        am.away_xga_per_match_last5,
        am.away_shots_conceded_per_match_last5,
        am.away_transition_threat_last5,
        am.away_set_piece_threat_last5,
        coalesce(hm.home_xg_delta_last5, 0) - coalesce(am.away_xg_delta_last5, 0)
            as xg_delta_edge_home,
        coalesce(hm.home_shot_quality_conversion_last5, 0)
        - coalesce(am.away_shot_quality_conversion_last5, 0)
            as shot_quality_conversion_edge_home,
        coalesce(am.away_xga_per_match_last5, 0)
        - coalesce(hm.home_xga_per_match_last5, 0)
            as defensive_suppression_edge_home,
        coalesce(hm.home_transition_threat_last5, 0)
        - coalesce(am.away_transition_threat_last5, 0)
            as transition_threat_edge_home,
        coalesce(hm.home_set_piece_threat_last5, 0)
        - coalesce(am.away_set_piece_threat_last5, 0)
            as set_piece_threat_edge_home,
        case
            when coalesce(hm.home_xg_delta_last5, 0) - coalesce(am.away_xg_delta_last5, 0) >= 0.25
                then 'HOME_CHANCE_EDGE'
            when coalesce(hm.home_xg_delta_last5, 0) - coalesce(am.away_xg_delta_last5, 0) <= -0.25
                then 'AWAY_CHANCE_EDGE'
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

select * from final
