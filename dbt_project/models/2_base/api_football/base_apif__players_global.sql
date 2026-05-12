-- Global player entity: one row per player_api_id (latest ingest across league_code rows).
-- Feeds dim_player. Grain: player_api_id.

select *
from {{ ref('base_apif__bl1_players') }}
qualify row_number() over (
    partition by player_api_id
    order by raw_ingested_at desc
) = 1
