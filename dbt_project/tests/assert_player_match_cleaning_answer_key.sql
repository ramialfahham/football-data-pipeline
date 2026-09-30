{#
  Hand-worked cases, one or more per cleaning rule, from the provider's raw values of real matches
  (seeds/player_match_cleaning_answer_key.csv: the row, the stat, the value worked out by hand and
  the rule it tests). base_apif__fixture_players must return exactly that value; a blank expected
  value means the rule must leave the stat blank. Returns each case whose value differs, and each
  case whose row is missing.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set stats = [
    'minutes', 'offsides', 'shots', 'shots_on_target', 'goals', 'goals_penalty', 'goals_against', 'assists',
    'saves', 'passes', 'passes_key', 'passes_accurate', 'tackles', 'blocks', 'interceptions', 'duels',
    'duels_won', 'dribbles', 'dribbles_success', 'dribbles_against', 'fouls', 'fouls_against',
    'cards_yellow', 'cards_red', 'penalties_won', 'penalties_committed', 'penalties_scored',
    'penalties_missed', 'penalties_saved'
] %}

with answer_key as (
    select * from {{ ref('player_match_cleaning_answer_key') }}
),

players as (
    select * from {{ ref('base_apif__fixture_players') }}
)

select
    k.fixture_id,
    k.team_id,
    k.player_id,
    k.stat,
    k.rule,
    k.expected_value,
    case k.stat
        {% for stat in stats %}
        when '{{ stat }}' then p.{{ stat }}
        {% endfor %}
    end as actual_value,
    p.player_id is null as row_missing
from answer_key as k
left join players as p
    on k.fixture_id = p.fixture_id and k.team_id = p.team_id and k.player_id = p.player_id
where
    p.player_id is null
    or k.stat not in ('{{ stats | join("', '") }}')
    or k.expected_value is distinct from case k.stat
        {% for stat in stats %}
        when '{{ stat }}' then p.{{ stat }}
        {% endfor %}
    end
