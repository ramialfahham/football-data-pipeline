{#
  True where a line is filed under a team that did not play the match: both of the match's teams
  are known and the line's team is neither. A line with no team, or a match with an unknown team,
  is not this defect.
#}
{% macro team_not_in_fixture(team_id, home_team_id, away_team_id) -%}
coalesce(
    {{ team_id }} is not null
    and {{ home_team_id }} is not null
    and {{ away_team_id }} is not null
    and {{ team_id }} not in ({{ home_team_id }}, {{ away_team_id }}),
    false
)
{%- endmacro %}
