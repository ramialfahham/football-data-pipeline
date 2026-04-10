with raw_players as (
    select
        league_code,
        payload_response
    from {{ ref('base_apif__players') }}
),
team_blocks as (
    select
        league_code,
        team_block
    from raw_players,
    unnest(payload_response) as team_block
),
players_flat as (
    select
        league_code,
        cast(team_block.team_id as int64) as team_source_id,
        player_entry
    from team_blocks,
    unnest(team_block.players_payload) as player_entry
),
prepared as (
    select
        league_code,
        team_source_id,
        cast(player_entry.player.id as int64) as player_source_id,
        cast(player_entry.player.name as string) as player_name,
        cast(player_entry.player.firstname as string) as first_name,
        cast(player_entry.player.lastname as string) as last_name,
        cast(player_entry.player.nationality as string) as nationality,
        cast(player_entry.player.age as int64) as age
    from players_flat
)

select distinct
    {{ dbt_utils.generate_surrogate_key(['league_code', 'cast(player_source_id as string)']) }} as player_id,
    league_code,
    player_source_id,
    team_source_id,
    player_name,
    first_name,
    last_name,
    nationality,
    age
from prepared
where player_source_id is not null
