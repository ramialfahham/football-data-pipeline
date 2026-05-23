-- Unified fixtures across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Output grain: fixture_id (deduplicated to latest ingest).
{% set league_codes = var('active_competition_league_codes') %}

with src as (

{% for lc in league_codes %}
    {% if not loop.first %}

    union all

    {% endif %}
    select *
    from {{ ref('stg_apif__' ~ lc | lower ~ '_fixtures_next') }}
    where fixture_id is not null

{% endfor %}

)

select
    league_code,
    fixture_id,
    league_api_id,
    season,
    fixture_date,
    kickoff_datetime,
    kickoff_timezone,
    status_short,
    status_long,
    status_elapsed,
    round_name,
    home_team_id,
    away_team_id,
    goals_home,
    goals_away,
    venue_id,
    venue_name,
    venue_city,
    raw_ingested_at
from src
qualify row_number() over (
    partition by fixture_id
    order by raw_ingested_at desc
) = 1
