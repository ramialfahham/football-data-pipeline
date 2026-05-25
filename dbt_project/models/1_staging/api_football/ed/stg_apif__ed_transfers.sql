with src as (
    select *
    from {{ apif_latest_source_partition('api_football', 'raw_apif_ed_transfers') }}
),

exploded as (
    select
        'ED' as league_code,
        src.ingested_at as raw_ingested_at,
        row_json,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json
    from src,
        unnest({{ apif_payload_response_json_strings('src') }}) as row_json
),

transfer_rows_raw as (
    select
        league_code,
        raw_ingested_at,
        api_errors_json,
        api_reported_result_count,
        request_parameters_json,
        row_json,
        transfer_el
    from exploded,
        unnest(
            coalesce(
                json_query_array(json_query(safe.parse_json(row_json), '$.transfers'), '$'),
                []
            )
        ) as transfer_el
),

transfer_rows as (
    select
        league_code,
        raw_ingested_at,
        api_errors_json,
        api_reported_result_count,
        request_parameters_json,
        row_json,
        transfer_el,
        safe_cast(json_value(row_json, '$.player.id') as int64) as player_id,
        json_value(row_json, '$.player.name') as player_name,
        json_value(row_json, '$.player.photo') as player_photo_url
    from transfer_rows_raw
)

select
    league_code,
    raw_ingested_at,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    row_json as source_json,
    player_id,
    player_name,
    player_photo_url,
    safe_cast(json_value(transfer_el, '$.date') as date) as transfer_date,
    json_value(transfer_el, '$.type') as transfer_type,
    safe_cast(json_value(transfer_el, '$.teams.out.id') as int64) as from_team_api_id,
    json_value(transfer_el, '$.teams.out.name') as from_team_name_snapshot,
    safe_cast(json_value(transfer_el, '$.teams.in.id') as int64) as to_team_api_id,
    json_value(transfer_el, '$.teams.in.name') as to_team_name_snapshot
from transfer_rows
where safe_cast(json_value(transfer_el, '$.date') as date) is not null
qualify row_number() over (
    partition by
        league_code,
        player_id,
        safe_cast(json_value(transfer_el, '$.date') as date),
        safe_cast(json_value(transfer_el, '$.teams.out.id') as int64),
        safe_cast(json_value(transfer_el, '$.teams.in.id') as int64),
        json_value(transfer_el, '$.type')
    order by raw_ingested_at desc
) = 1
