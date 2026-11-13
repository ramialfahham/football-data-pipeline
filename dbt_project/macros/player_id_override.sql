{#- The id a player keeps when the provider holds that player under two. -#}
{% macro player_id_override(player_id) -%}
    coalesce(
        (
            select override.correct_player_api_id
            from {{ ref('player_id_overrides') }} as override
            where override.mode = 'alias' and override.wrong_player_api_id = {{ player_id }}
        ),
        {{ player_id }}
    )
{%- endmacro %}

{#- The id of a player on a team's sheet or stat line of one match: the warehouse's own id where the
    provider holds the placeholder 0 for that shirt, otherwise the id he keeps. -#}
{% macro fixture_player_id(player_id, fixture_id, team_id, shirt_number) -%}
    coalesce(
        (
            select override.correct_player_api_id
            from {{ ref('player_id_overrides') }} as override
            where
                override.mode = 'assign_in_fixture'
                and override.wrong_player_api_id = coalesce({{ player_id }}, 0)
                and override.fixture_id = {{ fixture_id }}
                and override.team_id = {{ team_id }}
                and override.shirt_number = {{ shirt_number }}
        ),
        {{ player_id_override(player_id) }}
    )
{%- endmacro %}
