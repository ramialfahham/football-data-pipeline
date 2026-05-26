{{ config(materialized='table') }}

{# Finished fixtures as two team-rows with team stats and opponent aggregates. Grain: (fixture_sk, team_sk). #}

with import_fct_fixture as (
    select * from {{ ref('fct_fixture') }}
),

import_fct_fixture_team_stats as (
    select * from {{ ref('fct_fixture_team_stats') }}
),

finished_legs as (
    select
        f.fixture_sk,
        f.league_sk,
        f.season_sk,
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
    from import_fct_fixture as f
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and f.goals_home is not null
        and f.goals_away is not null
    union all
    select
        f.fixture_sk,
        f.league_sk,
        f.season_sk,
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
    from import_fct_fixture as f
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and f.goals_home is not null
        and f.goals_away is not null
),

finished_team_stats as (
    select
        fl.fixture_sk,
        fl.team_sk,
        fl.league_sk,
        fl.season_sk,
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
    left join import_fct_fixture_team_stats as stats
        on
            fl.fixture_sk = stats.fixture_sk
            and fl.team_sk = stats.team_sk
)

select
    fts.fixture_sk,
    fts.team_sk,
    fts.league_sk,
    fts.season_sk,
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
