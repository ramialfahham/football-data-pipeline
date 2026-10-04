{{ config(severity = 'error', store_failures = true) }}

-- A cleaned player row and that player's events in the same match under different teams. The
-- player's-team rule of the cleaning rules moves the side the squad list contradicts, so a row here
-- is a match the rule could not decide. Own goals are left out: the provider files them under the
-- team they count for.
select
    player_row.league_code,
    player_row.fixture_id,
    player_row.player_id,
    player_row.team_id as row_team_id,
    player_event.team_id as event_team_id,
    player_event.event_index,
    player_event.event_type
from {{ ref('base_apif__fixture_players') }} as player_row
inner join {{ ref('base_apif__fixture_events') }} as player_event
    on
        player_row.fixture_id = player_event.fixture_id
        and player_row.player_id = player_event.player_id
where
    player_event.team_id != player_row.team_id
    and not (player_event.event_type = 'Goal' and player_event.event_detail = 'Own Goal')
