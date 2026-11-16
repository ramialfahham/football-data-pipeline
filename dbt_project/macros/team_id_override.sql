{#- The id a club keeps when the provider holds that club under two. -#}
{% macro team_id_override(team_id) -%}
    coalesce(
        (
            select cast(override.correct_team_api_id as int64)
            from {{ ref('fixture_team_id_overrides') }} as override
            where override.mode = 'alias' and override.wrong_team_api_id = {{ team_id }}
        ),
        {{ team_id }}
    )
{%- endmacro %}
