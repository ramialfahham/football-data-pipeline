-- Unified standings across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Output grain: (league_code, season, team_id).
{% set league_codes = var('active_competition_league_codes') %}

with src as (

{% for lc in league_codes %}
    {% if not loop.first %}

    union all

    {% endif %}
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__' ~ lc | lower ~ '_standings') }}
    where
        team_id is not null
        and season is not null

{% endfor %}

),

deduped_standings as (
    select *
    from src
    qualify row_number() over (
        partition by league_code, season, team_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    league_api_id,
    league_name,
    season,
    team_id,
    team_name,
    standing_rank,
    points,
    goals_diff,
    form,
    group_description,
    played_all,
    wins_all,
    draws_all,
    losses_all,
    raw_ingested_at
from deduped_standings
