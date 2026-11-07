{#- A correction row wins even when its value is empty: empty means no source states the value. -#}
{% macro bio_correction(correction_alias, value) -%}
if({{ correction_alias }}.player_api_id is null, {{ value }}, {{ correction_alias }}.corrected_value)
{%- endmacro %}
