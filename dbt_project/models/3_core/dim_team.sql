{{ config(materialized='table') }}

with all_teams as (
    select * from {{ ref('base_apif__teams') }}
)

select
    cast(team_api_id as int64) as team_sk,
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
from all_teams
qualify row_number() over (
    partition by team_api_id
    order by raw_ingested_at desc
) = 1
