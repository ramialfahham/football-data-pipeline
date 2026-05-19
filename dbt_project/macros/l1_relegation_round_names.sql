{% macro l1_relegation_round_names_in_clause() %}
    (
        {%- for round_label in var('l1_relegation_round_names') -%}
            '{{ round_label }}'{% if not loop.last %}, {% endif %}
        {%- endfor -%}
    )
{% endmacro %}
