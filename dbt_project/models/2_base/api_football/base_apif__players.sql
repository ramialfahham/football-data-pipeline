-- Unified player entity rows across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Two sources per competition where available:
--   priority 1 — /players endpoint (biographical attributes, most complete)
--   priority 2 — transfers fallback (covers players known only from transfer history)
-- Output grain: (league_code, player_api_id) — one row per player per league.
-- base_apif__players_global deduplicates further to one row per player_api_id.
{% set league_codes = var('active_competition_league_codes') %}

with players_src as (

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
        raw_ingested_at,
        1 as source_priority
    from {{ ref('stg_apif__' ~ lc | lower ~ '_players') }}
    where player_id is not null

    {% endfor %}

),

-- Transfers fallback: provides player identity for players who appear in transfer
-- history but have no /players endpoint record. BL1 only for now; extend this CTE
-- when additional leagues gain transfer base models.
transfers_src as (
    select
        league_code,
        player_id as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        player_photo_url,
        cast(null as int64) as last_known_team_api_id,
        cast(null as int64) as last_known_season_year,
        raw_ingested_at,
        2 as source_priority
    from {{ ref('base_apif__bl1_transfers') }}
    where player_id is not null
),

src as (
    select * from players_src
    union all
    select * from transfers_src
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
        source_priority asc,
        last_known_season_year desc nulls last,
        last_known_team_api_id desc nulls last,
        raw_ingested_at desc
) = 1
