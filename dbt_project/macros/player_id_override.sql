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

{#- The id of a player on a team's sheet, stat line or event of one match: the id a researched row
    gives him in that match, otherwise the id he keeps. A row for the placeholder 0 names the shirt;
    a row for a provider id needs none, so a source without shirts passes NULL. -#}
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
                and (override.wrong_player_api_id != 0 or override.shirt_number = {{ shirt_number }})
        ),
        {{ player_id_override(player_id) }}
    )
{%- endmacro %}

{#- The id of a player on one /players season row: the id a researched row gives him in that
    competition, season and team, otherwise the id he keeps. -#}
{% macro season_player_id(player_id, league_code, season_year, team_id) -%}
    coalesce(
        (
            select override.correct_player_api_id
            from {{ ref('player_id_overrides') }} as override
            where
                override.mode = 'assign_in_season'
                and override.wrong_player_api_id = {{ player_id }}
                and override.league_code = {{ league_code }}
                and override.season_year = {{ season_year }}
                and override.team_id = {{ team_id }}
        ),
        {{ player_id_override(player_id) }}
    )
{%- endmacro %}
