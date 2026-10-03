{#
  A stat fact disagrees with its base: a row in one and not the other, or a value that differs.
  Each fact is its base keyed and renamed, rebuilt in full every night, so every column it takes
  from base must match on every row. One row per disagreeing row, with the side it is missing from.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set facts = [
    {'fact': 'fct_fixture_player_stats', 'base': 'base_apif__fixture_players',
     'renamed': {'fixture_api_id': 'fixture_id', 'team_api_id': 'team_id', 'player_api_id': 'player_id'},
     'columns': ['league_code', 'minutes', 'shirt_number', 'position_code', 'is_captain', 'is_substitute',
                 'offsides', 'shots', 'shots_on_target', 'goals', 'goals_penalty', 'goals_against',
                 'assists', 'saves', 'passes', 'passes_key', 'passes_accurate', 'tackles', 'blocks',
                 'interceptions', 'duels', 'duels_won', 'dribbles', 'dribbles_success',
                 'dribbles_against', 'fouls', 'fouls_against', 'cards_yellow', 'cards_red',
                 'penalties_won', 'penalties_committed', 'penalties_scored', 'penalties_missed',
                 'penalties_saved', 'raw_ingested_at']},
    {'fact': 'fct_fixture_team_stats', 'base': 'base_apif__fixture_statistics',
     'renamed': {'fixture_api_id': 'fixture_id', 'team_api_id': 'team_id'},
     'columns': ['league_code', 'has_stat_line', 'shots_on_target', 'shots_off_target', 'shots',
                 'shots_blocked', 'shots_inside_box', 'shots_outside_box', 'fouls', 'corners',
                 'offsides', 'possession_pct', 'cards_yellow', 'cards_red', 'saves', 'passes',
                 'passes_accurate', 'goals_penalty', 'goals_own', 'raw_ingested_at']},
] %}

{% for f in facts %}
{% set fact_columns %}{% for k in f['renamed'] %}{{ k }}, {% endfor %}{{ f['columns'] | join(', ') }}{% endset %}
{% set base_columns %}{% for k, v in f['renamed'].items() %}{{ v }} as {{ k }}, {% endfor %}{{ f['columns'] | join(', ') }}{% endset %}
select
    '{{ f.fact }}' as fact,
    'missing from base' as side,
    to_json_string(t) as fact_row
from (
    select {{ fact_columns }} from {{ ref(f.fact) }}
    except distinct
    select {{ base_columns }} from {{ ref(f.base) }}
) as t

union all

select
    '{{ f.fact }}' as fact,
    'missing from the fact' as side,
    to_json_string(t) as fact_row
from (
    select {{ base_columns }} from {{ ref(f.base) }}
    except distinct
    select {{ fact_columns }} from {{ ref(f.fact) }}
) as t
{% if not loop.last %}

union all

{% endif %}
{% endfor %}
