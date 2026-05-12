{{
    config(
        materialized='view',
        tags=['debug'],
        enabled=true
    )
}}

-- Debug view: one row per (upcoming fixture, side, form game).
-- Shows exactly which 5 games feed each team's form metrics.
-- Run locally to verify metric inputs against external reference data (e.g. kicker.de).
-- Excluded from CI deploy via --exclude tag:debug.

with

import_int_matchday__upcoming_round_fixtures as (
    select * from {{ ref('int_matchday__upcoming_round_fixtures') }}
),

import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

upcoming_matchday as (
    select * from import_int_matchday__upcoming_round_fixtures
),

team_context as (
    select
        fixture_sk as upcoming_fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime as upcoming_kickoff,
        upcoming_round_order,
        round_name as upcoming_round,
        home_team_sk as team_sk,
        home_team_name as team_name,
        away_team_name as opponent_name,
        'home' as side
    from upcoming_matchday
    union all
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        upcoming_round_order,
        round_name,
        away_team_sk,
        away_team_name,
        home_team_name,
        'away' as side
    from upcoming_matchday
),

finished_legs as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        round_order,
        team_sk,
        goals_for,
        goals_against,
        result
    from import_int_matchday__finished_fixture_team_leg
),

ranked as (
    select
        tc.upcoming_fixture_sk,
        tc.upcoming_round,
        tc.side,
        tc.team_name,
        tc.opponent_name,
        fl.fixture_sk as form_fixture_sk,
        fl.round_name as form_round,
        fl.kickoff_datetime as form_kickoff,
        fl.goals_for,
        fl.goals_against,
        fl.result,
        dense_rank() over (
            partition by tc.upcoming_fixture_sk, tc.team_sk
            order by fl.round_order desc nulls last, fl.kickoff_datetime desc
        ) as rank_in_window
    from team_context as tc
    inner join finished_legs as fl
        on
            tc.team_sk = fl.team_sk
            and tc.league_code = fl.league_code
            and tc.season_api_year = fl.season_api_year
            and tc.upcoming_kickoff > fl.kickoff_datetime
            and (
                tc.upcoming_round_order is null
                or fl.round_order is null
                or tc.upcoming_round_order > fl.round_order
            )
)

select *
from ranked
where rank_in_window <= 5
order by upcoming_fixture_sk, side, rank_in_window
