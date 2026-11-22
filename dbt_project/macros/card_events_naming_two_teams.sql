{#
  The players whose card events in one match name two teams. The provider marks a coach's card
  "Not on pitch", which is no player's card; the events count only where the match has full events.

  events: a relation with fixture_id, player_id, team_id, event_type, event_comments and
  has_full_events, taken as text so a test can pass hand-written rows.
  Returns one row per match and player: fixture_id, player_id.
#}
{% macro card_events_naming_two_teams(events) -%}
select
    fixture_id,
    player_id
from {{ events }}
where
    event_type = 'Card'
    and coalesce(event_comments, '') != 'Not on pitch'
    and has_full_events
    and player_id is not null
group by fixture_id, player_id
having count(distinct team_id) > 1
{%- endmacro %}
