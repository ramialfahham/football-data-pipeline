{% macro team_name_key(team_name_expr) -%}
trim(
    regexp_replace(
        regexp_replace(
            regexp_replace(
                lower(
                    normalize(cast({{ team_name_expr }} as string), NFKD)
                ),
                r'[\u0300-\u036f]',
                ''
            ),
            r'[^a-z0-9 ]',
            ' '
        ),
        r'\s+',
        ' '
    )
)
{%- endmacro %}
