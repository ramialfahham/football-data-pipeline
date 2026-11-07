{#- The id a player keeps when the provider holds that player under two. -#}
{% macro player_id_override(player_id) -%}
    coalesce(
        (
            select override.correct_player_api_id
            from {{ ref('player_id_overrides') }} as override
            where override.wrong_player_api_id = {{ player_id }}
        ),
        {{ player_id }}
    )
{%- endmacro %}
