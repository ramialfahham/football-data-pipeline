with src as (
    select * from {{ ref('stg_apif__wc26_teams') }}
    where team_id is not null
)

select
    league_code,
    team_id as team_api_id,
    team_code,
    team_country,
    founded_year as team_founded_year,
    team_logo_url,
    venue_id as venue_api_id,
    venue_name,
    venue_address,
    venue_city,
    venue_capacity,
    team_name,
    raw_ingested_at
from src
qualify row_number() over (
    partition by league_code, team_id
    order by season desc, raw_ingested_at desc
) = 1
