{% macro domestic_league_codes_in_clause() %}
    {%- set codes = [] -%}
    {%- for code in var('active_competition_league_codes') -%}
        {%- if code != 'WC' and not code.startswith('WCQ') -%}
            {%- do codes.append(code) -%}
        {%- endif -%}
    {%- endfor -%}
    (
        {%- for code in codes -%}
            '{{ code }}'{% if not loop.last %}, {% endif %}
        {%- endfor -%}
    )
{% endmacro %}
