-- Every name and place column, where it first becomes a column: one row per value that still holds
-- an HTML entity, such as one decode_html_entities does not know. Later layers copy these columns.
{%- set name_columns = [
    ('stg_apif__coach_career', 'team_name'),
    ('stg_apif__coaches', 'coach_name'),
    ('stg_apif__coaches', 'coach_first_name'),
    ('stg_apif__coaches', 'coach_last_name'),
    ('stg_apif__coaches', 'coach_birth_place'),
    ('stg_apif__coaches', 'coach_birth_country'),
    ('stg_apif__coaches', 'coach_nationality'),
    ('stg_apif__fixture_events', 'team_name'),
    ('stg_apif__fixture_events', 'player_name'),
    ('stg_apif__fixture_events', 'assist_player_name'),
    ('stg_apif__fixture_players', 'team_name'),
    ('stg_apif__fixture_players', 'player_name'),
    ('stg_apif__fixture_statistics', 'team_name'),
    ('stg_apif__fixtures_next', 'league_name'),
    ('stg_apif__fixtures_next', 'home_team_name'),
    ('stg_apif__fixtures_next', 'away_team_name'),
    ('stg_apif__fixtures_next', 'venue_name'),
    ('stg_apif__fixtures_next', 'venue_city'),
    ('stg_apif__leagues', 'league_name'),
    ('stg_apif__leagues', 'country'),
    ('stg_apif__lineups', 'team_name'),
    ('stg_apif__lineups', 'coach_name'),
    ('stg_apif__player_profiles', 'player_name'),
    ('stg_apif__player_profiles', 'player_firstname'),
    ('stg_apif__player_profiles', 'player_lastname'),
    ('stg_apif__player_profiles', 'birth_place'),
    ('stg_apif__player_profiles', 'birth_country'),
    ('stg_apif__player_profiles', 'nationality'),
    ('stg_apif__player_teams', 'team_name'),
    ('stg_apif__players', 'player_name'),
    ('stg_apif__players', 'player_firstname'),
    ('stg_apif__players', 'player_lastname'),
    ('stg_apif__players', 'nationality'),
    ('stg_apif__squads', 'player_name'),
    ('stg_apif__standings', 'league_name'),
    ('stg_apif__standings', 'team_name'),
    ('stg_apif__teams', 'team_name'),
    ('stg_apif__teams', 'team_country'),
    ('stg_apif__teams', 'venue_name'),
    ('stg_apif__teams', 'venue_address'),
    ('stg_apif__teams', 'venue_city'),
    ('base_apif__lineups', 'player_name'),
] %}
{% for model_name, column_name in name_columns %}
select distinct
    '{{ model_name }}' as model_name,
    '{{ column_name }}' as column_name,
    {{ column_name }} as name_value
from {{ ref(model_name) }}
where regexp_contains({{ column_name }}, r'&#?[A-Za-z0-9]+;')
{% if not loop.last %}union all{% endif %}
{% endfor %}
