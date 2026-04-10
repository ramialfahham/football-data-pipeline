with source as (
    select *
    from {{ source('football_data_org', 'raw_fdorg_matches_scheduled_pd') }}
)

select
    'PD' as competition_code,
    filters as request_filters,
    resultSet as result_set,
    competition as competition_info,
    matches as matches_payload
from source
