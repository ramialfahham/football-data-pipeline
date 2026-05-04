with src as (
    select * from {{ ref('stg_apif__bl1_transfers') }}
    where player_id is not null
)

select
    league_code,
    player_id,
    player_name,
    player_photo_url,
    transfer_date,
    transfer_type,
    from_team_api_id,
    from_team_name_snapshot,
    to_team_api_id,
    to_team_name_snapshot,
    raw_ingested_at,
    source_json,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json
from src
qualify row_number() over (
    partition by
        league_code,
        player_id,
        transfer_date,
        from_team_api_id,
        to_team_api_id,
        transfer_type
    order by raw_ingested_at desc
) = 1
