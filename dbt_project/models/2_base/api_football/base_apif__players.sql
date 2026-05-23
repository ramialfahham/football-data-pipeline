-- Unified player entity rows across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Output grain: (league_code, player_api_id) — one row per player per league.
-- base_apif__players_global deduplicates further to one row per player_api_id.
{% set league_codes = var('active_competition_league_codes') %}

with src as (

    {% for lc in league_codes %}
    {% if not loop.first %}

    union all

    {% endif %}
    select
        league_code,
        safe_cast(player_id as int64) as player_api_id,
        player_name,
        player_firstname as player_first_name,
        player_lastname as player_last_name,
        birth_date as player_birth_date,
        nationality as player_nationality,
        player_photo_url,
        safe_cast(team_id as int64) as last_known_team_api_id,
        safe_cast(season_year as int64) as last_known_season_year,
        raw_ingested_at
    from {{ ref('stg_apif__' ~ lc | lower ~ '_players') }}
    where player_id is not null

    {% endfor %}

)

select
    league_code,
    player_api_id,
    player_name,
    player_first_name,
    player_last_name,
    player_birth_date,
    player_nationality,
    player_photo_url,
    last_known_team_api_id,
    last_known_season_year,
    raw_ingested_at
from src
qualify row_number() over (
    partition by league_code, player_api_id
    order by
        last_known_season_year desc nulls last,
        last_known_team_api_id desc nulls last,
        raw_ingested_at desc
) = 1
