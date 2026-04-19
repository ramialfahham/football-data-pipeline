{{ config(materialized='table') }}

with src as (
    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__d1_teams') }}
    where team_id is not null
),

ranked as (
    select
        *,
        row_number() over (
            partition by league_code, team_api_id
            order by season desc, raw_ingested_at desc
        ) as rn
    from src
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'team_api_id']) }} as team_sk,
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
from ranked
where rn = 1
