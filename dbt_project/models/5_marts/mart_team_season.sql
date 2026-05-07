{{ config(materialized='table') }}

{#
    Per-team, per-season rollup. Counts derive from finished matches only
    (status_short in FT, AET, PEN) so unplayed fixtures don't skew aggregates.
    Latest rank joins from fct_standings; teams absent from the current
    standings snapshot (e.g. historical seasons) get null.
#}

with fct_fixture as (
    select * from {{ ref('fct_fixture') }}
),

dim_team as (
    select * from {{ ref('dim_team') }}
),

fct_standings as (
    -- The snapshot keeps one row per (team, season, group_description); when a
    -- team moves between zones (Champions League → Europa League etc.) the old
    -- zone row stays as dbt_valid_to=null. Picking min(standing_rank) here used
    -- to surface the team's best historical rank across zones (e.g. Stuttgart
    -- shown as rank 4 from a stale CL-zone row when the current EL-zone row
    -- says rank 5). Pick the most recently snapshot-validated row instead.
    select
        team_sk,
        season_sk,
        standing_rank,
        form
    from {{ ref('fct_standings') }}
    qualify row_number() over (
        partition by team_sk, season_sk order by snapshot_valid_from desc nulls last
    ) = 1
),

finished as (
    select
        fixture_sk,
        league_sk,
        season_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year,
        goals_home,
        goals_away
    from fct_fixture
    where status_short in ('FT', 'AET', 'PEN')
),

legs as (
    select
        home_team_sk as team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        fixture_sk,
        goals_home as goals_for,
        goals_away as goals_against,
        case
            when goals_home > goals_away then 'W'
            when goals_home < goals_away then 'L'
            else 'D'
        end as result
    from finished
    union all
    select
        away_team_sk as team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        fixture_sk,
        goals_away as goals_for,
        goals_home as goals_against,
        case
            when goals_away > goals_home then 'W'
            when goals_away < goals_home then 'L'
            else 'D'
        end as result
    from finished
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
    st.form as latest_form
from agg
left join dim_team as t on agg.team_sk = t.team_sk
left join fct_standings as st
    on agg.team_sk = st.team_sk and agg.season_sk = st.season_sk
