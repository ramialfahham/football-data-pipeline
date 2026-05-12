-- One row per (league_api_id, season_api_year); tie-break by latest ingest.
-- Collapses rare duplicate keys across league_code rows before dim_competition_season.
-- Grain: (league_api_id, season_api_year).

select *
from {{ ref('base_apif__leagues') }}
qualify row_number() over (
    partition by league_api_id, season_api_year
    order by raw_ingested_at desc
) = 1
