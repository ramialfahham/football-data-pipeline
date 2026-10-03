{#
  Hand-worked cases, one or more per cleaning rule, from the provider's raw values of real matches
  (seeds/team_match_cleaning_answer_key.csv: the team-match, the stat, the value worked out by hand
  and the rule it tests). base_apif__fixture_statistics must return exactly that value; a blank
  expected value means the rule must leave the stat blank. Returns each case whose value differs,
  and each case whose row is missing.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set stats = [
    'shots_on_target', 'shots_off_target', 'shots', 'shots_blocked', 'shots_inside_box', 'shots_outside_box',
    'fouls', 'corners', 'offsides', 'possession_pct', 'cards_yellow', 'cards_red', 'saves', 'passes',
    'passes_accurate', 'goals_penalty', 'goals_own'
] %}

with answer_key as (
    select * from {{ ref('team_match_cleaning_answer_key') }}
),

lines as (
    select * from {{ ref('base_apif__fixture_statistics') }}
)

select
    k.fixture_id,
    k.team_id,
    k.stat,
    k.rule,
    k.expected_value,
    case k.stat
        {% for stat in stats %}
        when '{{ stat }}' then l.{{ stat }}
        {% endfor %}
    end as actual_value,
    l.team_id is null as row_missing
from answer_key as k
left join lines as l
    on k.fixture_id = l.fixture_id and k.team_id = l.team_id
where
    l.team_id is null
    or k.stat not in ('{{ stats | join("', '") }}')
    or k.expected_value is distinct from case k.stat
        {% for stat in stats %}
        when '{{ stat }}' then l.{{ stat }}
        {% endfor %}
    end
