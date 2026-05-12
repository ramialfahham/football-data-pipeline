-- Global team entity: one row per team_api_id (latest ingest across league_code rows).
-- Feeds dim_team. Grain: team_api_id.

select *
from {{ ref('base_apif__teams') }}
qualify row_number() over (
    partition by team_api_id
    order by raw_ingested_at desc
) = 1
