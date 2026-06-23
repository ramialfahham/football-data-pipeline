{{ config(materialized='table') }}

{#
    Per-team, per-season rollup for table display and marts. The season counts COMPOSE the
    canonical rollup int_team_season__metrics (finished matches only via int_legs__team_match) —
    the same aggregation, not recomputed (#500 dedup). latest_rank, latest_form and
    standings_group_description join from int_team_season__standings_primary; teams absent from
    standings get nulls.
#}

with season_metrics as (
    select * from {{ ref('int_team_season__metrics') }}
),

dim_team as (
    select * from {{ ref('dim_team') }}
),

import_int_team_season__standings_primary as (
    select * from {{ ref('int_team_season__standings_primary') }}
)

select
    m.team_season_sk,
    m.team_sk,
    m.season_sk,
    m.league_sk,
    m.league_code,
    m.season_api_year,
    t.team_name,
    t.team_code,
    t.team_country,
    t.team_logo_url,
    m.season_games_played as played,
    m.wins_sum_season as wins,
    m.draws_sum_season as draws,
    m.losses_sum_season as losses,
    m.goals_for_sum_season as goals_for,
    m.goals_against_sum_season as goals_against,
    m.points_won_sum_season as points,
    m.clean_sheets_sum_season as clean_sheets,
    st.standing_rank as latest_rank,
    st.form as latest_form,
    st.group_description as standings_group_description,
    m.goals_for_sum_season - m.goals_against_sum_season as goal_diff
from season_metrics as m
left join dim_team as t on m.team_sk = t.team_sk
left join import_int_team_season__standings_primary as st
    on m.team_sk = st.team_sk and m.season_sk = st.season_sk
