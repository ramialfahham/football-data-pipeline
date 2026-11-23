{#
  The players whose stat line and match events, own goals aside, name different teams of the match.
  A hand-corrected goal or card is no provider event and is left out. Both teams are teams of the
  match, so an event under a team of another match is not a dispute here.

  player_rows: a relation with fixture_id, player_id and team_id.
  events: a relation with fixture_id, player_id, team_id, event_type, event_detail,
  goal_correction_source and card_correction_source.
  participants: a relation with fixture_id, home_team_id and away_team_id.
  Each is taken as text, so a test can pass hand-written rows.
  Returns one row per match and player: fixture_id, player_id.
#}
{% macro player_team_disputes(player_rows, events, participants) -%}
select distinct
    r.fixture_id,
    r.player_id
from {{ player_rows }} as r
inner join {{ events }} as e
    on r.fixture_id = e.fixture_id and r.player_id = e.player_id
inner join {{ participants }} as p
    on r.fixture_id = p.fixture_id
where
    e.team_id != r.team_id
    and r.team_id in (p.home_team_id, p.away_team_id)
    and e.team_id in (p.home_team_id, p.away_team_id)
    and not (e.event_type = 'Goal' and e.event_detail = 'Own Goal')
    and e.goal_correction_source is null
    and e.card_correction_source is null
{%- endmacro %}
