{#
  True where the score of a match decided after extra time stopped at 90 minutes: the goal events of
  the first 90 minutes add up to the score of each team, every goal has a minute, and an open-play
  goal or an own goal after minute 90 exists. A penalty after minute 90 is no evidence, because the
  provider files some shoot-outs as penalty goals without the shoot-out label.
#}
{% macro score_stopped_at_90(
    goals_home, goals_away, home_goals_in_90, away_goals_in_90, open_play_goals_after_90, goals_without_minute
) -%}
coalesce(
    {{ goals_without_minute }} = 0
    and {{ open_play_goals_after_90 }} > 0
    and {{ home_goals_in_90 }} = {{ goals_home }}
    and {{ away_goals_in_90 }} = {{ goals_away }},
    false
)
{%- endmacro %}
