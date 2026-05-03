{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'team_api_id']) }}  as team_sk,
    league_code,
    team_api_id,
    team_name,
    team_code,
    team_country,
    team_founded_year,
    team_logo_url,
    venue_api_id,
    venue_name,
    venue_address,
    venue_city,
    venue_capacity,
    raw_ingested_at
from {{ ref('base_apif__bl1_teams') }}
