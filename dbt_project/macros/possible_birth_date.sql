{#- A date under 13 years before the record was ingested is the provider's placeholder: empty. -#}
{% macro possible_birth_date(birth_date, ingested_at) -%}
    if(
        {{ birth_date }} > date_sub(date({{ ingested_at }}), interval 13 year),
        cast(null as date),
        {{ birth_date }}
    )
{%- endmacro %}
