with src as (
    select *
    from {{ source('api_football', 'raw_apif_transfers') }}
    qualify row_number() over (partition by league_code order by ingested_at desc) = 1
),

team_blocks as (
    select
        src.ingested_at as raw_ingested_at,
        team_block,
        src.league_code
    from src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as team_block
),

player_rows as (
    select
        league_code,
        raw_ingested_at,
        player_el
    from team_blocks,
        unnest(
            json_query_array(json_query(team_block, '$.transfers_payload'), '$')
        ) as player_el
),

transfer_rows as (
    select
        league_code,
        raw_ingested_at,
        transfer_el,
        safe_cast(json_value(player_el, '$.player.id') as int64) as player_id
    from player_rows,
        unnest(
            json_query_array(json_query(player_el, '$.transfers'), '$')
        ) as transfer_el
)

select
    league_code,
    raw_ingested_at,
    player_id,
    safe_cast(json_value(transfer_el, '$.date') as date) as transfer_date,
    json_value(transfer_el, '$.type') as transfer_type,
    safe_cast(json_value(transfer_el, '$.teams.in.id') as int64) as team_in_id,
    safe_cast(json_value(transfer_el, '$.teams.out.id') as int64) as team_out_id
from transfer_rows
