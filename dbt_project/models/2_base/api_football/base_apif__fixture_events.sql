-- Unified fixture events across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Output grain: (league_code, fixture_id, event_index).
{% set league_codes = var('active_competition_league_codes') %}

with src as (

    {% for lc in league_codes %}
    {% if not loop.first %}

    union all

    {% endif %}
    select
        league_code,
        fixture_id,
        event_index,
        minute_elapsed,
        minute_extra,
        team_id,
        team_name,
        player_id,
        player_name,
        assist_player_name,
        event_type,
        event_detail,
        event_comments,
        raw_ingested_at
    from {{ ref('stg_apif__' ~ lc | lower ~ '_fixture_events') }}
    where
        fixture_id is not null

    {% endfor %}

)

select
    league_code,
    fixture_id,
    event_index,
    minute_elapsed,
    minute_extra,
    team_id,
    team_name,
    player_id,
    player_name,
    assist_player_name,
    event_type,
    event_detail,
    event_comments,
    raw_ingested_at
from src
qualify row_number() over (
    partition by league_code, fixture_id, event_index
    order by raw_ingested_at desc
) = 1
