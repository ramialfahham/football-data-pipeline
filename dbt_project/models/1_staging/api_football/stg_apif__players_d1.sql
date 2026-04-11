with source as (
    select *
    from {{ source('api_football', 'raw_apif_players_d1') }}
)

select
    'D1' as league_code,
    cast(null as string) as api_endpoint,
    cast(null as json) as request_parameters,
    cast(null as json) as api_errors,
    cast(null as int64) as result_count,
    cast(null as json) as paging_info,
    response as payload_response
from source
