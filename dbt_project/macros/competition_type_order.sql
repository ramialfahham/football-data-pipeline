{#
  A competition's place among a team's or a player's competitions: domestic league first.
#}
{% macro competition_type_order(competition_type) %}
    case {{ competition_type }}
        when 'domestic_league' then 1
        when 'domestic_cup' then 2
        when 'domestic_super_cup' then 3
        else 4
    end
{% endmacro %}
