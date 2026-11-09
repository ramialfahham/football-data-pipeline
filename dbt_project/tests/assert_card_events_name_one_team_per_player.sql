{#
  base_apif__fixture_players takes a carded player's team as min(team_id) over their card events in a
  match. That is exact only while a player's cards in one match name one team; this fails any
  player whose cards name two.
#}
{{ config(store_failures = true, severity = 'error') }}

select
    fixture_id,
    player_id,
    count(distinct team_id) as teams
from {{ ref('base_apif__fixture_events') }}
where
    event_type = 'Card'
    and player_id is not null
group by fixture_id, player_id
having count(distinct team_id) > 1
