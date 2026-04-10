with source as (
    select *
    from {{ source('football_data_org', 'raw_fdorg_teams_bl1') }}
)

select
    'BL1' as competition_code,
    count as payload_count,
    filters as request_filters,
    competition as competition_info,
    season as season_info,
    teams as teams_payload
from source
