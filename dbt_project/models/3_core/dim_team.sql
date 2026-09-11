{{ config(materialized='table') }}

with import_base_apif__teams_global as (
    select * from {{ ref('base_apif__teams_global') }}
)

-- team_slug is the team's permanent, locale-independent URL segment
-- (/{locale}/teams/{team_slug}/, docs/site_architecture.md section 3). Derived in base and
-- merely published here, like every other attribute: base prepares, the dim propagates.
-- It carries no provider id except in the terminal collision case.
select
    cast(team_api_id as int64) as team_sk,
    team_api_id,
    team_name,
    team_slug,
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
from import_base_apif__teams_global
