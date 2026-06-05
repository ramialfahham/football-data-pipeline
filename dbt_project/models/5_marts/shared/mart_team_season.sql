{{ config(materialized='table') }}

{#
    Per-team, per-season rollup. Counts derive from finished matches only
    (FT/AET/PEN, null goals excluded) via int_legs__team_match.
    latest_rank, latest_form, and standings_group_description join from
    int_team_season__standings_primary; teams absent from standings get nulls.
#}

with team_legs as (
    select * from {{ ref('int_legs__team_match') }}
),

dim_team as (
    select * from {{ ref('dim_team') }}
),

import_int_team_season__standings_primary as (
    select * from {{ ref('int_team_season__standings_primary') }}
),

legs as (
    select
        team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        fixture_sk,
        goals_for,
        goals_against,
        result
    from team_legs
),

agg as (
    select
        team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        count(*) as played,
        countif(result = 'W') as wins,
        countif(result = 'D') as draws,
        countif(result = 'L') as losses,
        sum(coalesce(goals_for, 0)) as goals_for,
        sum(coalesce(goals_against, 0)) as goals_against,
        sum(coalesce(goals_for, 0)) - sum(coalesce(goals_against, 0)) as goal_diff,
        countif(result = 'W') * 3 + countif(result = 'D') as points,
        countif(coalesce(goals_against, 0) = 0) as clean_sheets
    from legs
    group by
        team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year
)

select
    {{ dbt_utils.generate_surrogate_key(['agg.team_sk', 'agg.season_sk']) }} as team_season_sk,
    agg.team_sk,
    agg.season_sk,
    agg.league_sk,
    agg.league_code,
    agg.season_api_year,
    t.team_name,
    t.team_code,
    t.team_country,
    t.team_logo_url,
    agg.played,
    agg.wins,
    agg.draws,
    agg.losses,
    agg.goals_for,
    agg.goals_against,
    agg.goal_diff,
    agg.points,
    agg.clean_sheets,
    st.standing_rank as latest_rank,
    st.form as latest_form,
    st.group_description as standings_group_description
from agg
left join dim_team as t on agg.team_sk = t.team_sk
left join import_int_team_season__standings_primary as st
    on agg.team_sk = st.team_sk and agg.season_sk = st.season_sk
