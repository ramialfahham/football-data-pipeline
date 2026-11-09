{#
  The one value a group holds, as min(column); the build fails if the group holds two. For a
  column the group key fixes, so a wrong join or grain fails loudly instead of picking one value.
#}
{% macro one_value(column) -%}
    if(
        count(distinct {{ column }}) > 1,
        error('one_value: {{ column | replace("'", "") }} holds two values in one group'),
        min({{ column }})
    )
{%- endmacro %}
