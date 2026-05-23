-- Global player entity: one row per player_api_id (latest ingest across league_code rows).
-- Reads from base_apif__players (unified across all active competitions).
-- Feeds dim_player. Grain: player_api_id.

select *
from {{ ref('base_apif__players') }}
qualify row_number() over (
    partition by player_api_id
    order by
        last_known_season_year desc nulls last,
        last_known_team_api_id desc nulls last,
        raw_ingested_at desc
) = 1
