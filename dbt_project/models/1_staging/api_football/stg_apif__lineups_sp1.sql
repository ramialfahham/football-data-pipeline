with source as (
    select *
    from {{ source('api_football', 'raw_apif_lineups_sp1') }}
)

select
    'SP1' as league_code,
    `get` as api_endpoint,
    parameters as request_parameters,
    errors as api_errors,
    results as result_count,
    paging as paging_info,
    response as payload_response
from source
