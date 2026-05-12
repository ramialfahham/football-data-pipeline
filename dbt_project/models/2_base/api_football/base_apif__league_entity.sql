-- One row per league_api_id: latest season row by season_api_year then ingest time.
-- Entity resolution for dim_league. Grain: league_api_id.

select *
from {{ ref('base_apif__leagues') }}
qualify row_number() over (
    partition by league_api_id
    order by season_api_year desc, raw_ingested_at desc
) = 1
