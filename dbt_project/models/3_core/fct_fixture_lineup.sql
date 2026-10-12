with src as (
    select * from {{ ref('base_apif__lineups') }}
)

select
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
    cast(player_id as int64) as player_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    player_id as player_api_id,
    is_starter,
    shirt_number,
    position_code,
    grid_position,
    team_formation,
    minute_on,
    minute_on_extra,
    cast(replaced_player_id as int64) as replaced_player_sk,
    minute_off,
    minute_off_extra,
    lineup_state
from src
