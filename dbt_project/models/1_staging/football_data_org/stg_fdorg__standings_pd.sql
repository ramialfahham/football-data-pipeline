with source as (
    select *
    from {{ source('football_data_org', 'raw_fdorg_standings_pd') }}
)

select
    'PD' as competition_code,
    filters as request_filters,
    area as area_info,
    competition as competition_info,
    season as season_info,
    standings as standings_payload
from source
