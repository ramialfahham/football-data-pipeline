{#
  A stat fact disagrees with its base: a row in one and not the other, or a value that differs.
  Each fact is its base keyed and renamed, rebuilt in full every night, so every column it takes
  from base must match on every row. One row per disagreeing row, with the side it is missing from.
  The team fact also holds sides that base has no row for, with no stat columns and no ingest
  time; those rows are left out of the comparison. A base line filed under a team that did not
  play the match is left out of its fact, so it is left out of the base side here. Which lines
  those are is derived from the match's two teams in fct_fixture, never from the flag, so a flag
  that withholds a line of a team of the match still fails this test. assert_misfiled_team_lines_withheld
  holds the withheld lines to account. A player line of a player whose stat line and events name the
  two different teams of the match is left out of its fact too, and out of the base side here, by the
  same inline derivation; assert_player_row_and_events_same_team holds those lines to account.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set player_keys = {'fixture_api_id': 'fixture_id', 'team_api_id': 'team_id', 'player_api_id': 'player_id'} %}
{% set player_columns = ['league_code', 'minutes', 'shirt_number', 'position_code', 'is_captain', 'is_substitute',
                 'offsides', 'shots', 'shots_on_target', 'goals', 'goals_penalty', 'goals_against',
                 'assists', 'saves', 'passes', 'passes_key', 'passes_accurate', 'tackles', 'blocks',
                 'interceptions', 'duels', 'duels_won', 'dribbles', 'dribbles_success',
                 'dribbles_against', 'fouls', 'fouls_against', 'cards_yellow', 'cards_red',
                 'penalties_won', 'penalties_committed', 'penalties_scored', 'penalties_missed',
                 'penalties_saved', 'raw_ingested_at'] %}
{% set facts = [
    {'fact': 'fct_fixture_player_stats', 'base': 'base_apif__fixture_players_checked',
     'fact_rows': 'not is_from_lineups', 'renamed': player_keys, 'columns': player_columns},
    {'fact': 'fct_fixture_player_stats', 'base': 'base_apif__fixture_players_from_lineups',
     'fact_rows': 'is_from_lineups', 'renamed': player_keys, 'columns': player_columns},
    {'fact': 'fct_fixture_team_stats', 'base': 'base_apif__fixture_statistics',
     'fact_rows': 'raw_ingested_at is not null',
     'renamed': {'fixture_api_id': 'fixture_id', 'team_api_id': 'team_id'},
     'columns': ['league_code', 'has_stat_line', 'shots_on_target', 'shots_off_target', 'shots',
                 'shots_blocked', 'shots_inside_box', 'shots_outside_box', 'fouls', 'corners',
                 'offsides', 'free_kicks', 'possession_pct', 'cards_yellow', 'cards_red', 'saves', 'passes',
                 'passes_accurate', 'goals_penalty', 'goals_own', 'raw_ingested_at']},
] %}

with participants as (
    select
        fixture_api_id as fixture_id,
        home_team_api_id as home_team_id,
        away_team_api_id as away_team_id
    from {{ ref('fct_fixture') }}
),

disputes as (
    select distinct
        r.fixture_id,
        r.player_id
    from {{ ref('base_apif__fixture_players') }} as r
    inner join {{ ref('base_apif__fixture_events') }} as e
        on r.fixture_id = e.fixture_id and r.player_id = e.player_id
    inner join participants as p
        on r.fixture_id = p.fixture_id
    where
        e.team_id != r.team_id
        and r.team_id in (p.home_team_id, p.away_team_id)
        and e.team_id in (p.home_team_id, p.away_team_id)
        and not (e.event_type = 'Goal' and e.event_detail = 'Own Goal')
        and e.goal_correction_source is null
        and e.card_correction_source is null
)

{% for f in facts %}
{% set fact_columns %}{% for k in f['renamed'] %}{{ k }}, {% endfor %}{{ f['columns'] | join(', ') }}{% endset %}
{% set base_columns %}{% for k, v in f['renamed'].items() %}{{ v }} as {{ k }}, {% endfor %}{{ f['columns'] | join(', ') }}{% endset %}
select
    '{{ f.fact }}' as fact,
    'missing from base' as side,
    to_json_string(t) as fact_row
from (
    select {{ fact_columns }} from {{ ref(f.fact) }} where {{ f.fact_rows }}
    except distinct
    select {{ base_columns }} from {{ ref(f.base) }}
) as t

union all

select
    '{{ f.fact }}' as fact,
    'missing from the fact' as side,
    to_json_string(t) as fact_row
from (
    select {{ base_columns }}
    from {{ ref(f.base) }} as b
    where not exists (
        select 1
        from participants as p
        where
            p.fixture_id = b.fixture_id
            and b.team_id is not null
            and p.home_team_id is not null
            and p.away_team_id is not null
            and b.team_id not in (p.home_team_id, p.away_team_id)
    )
    {%- if 'player_api_id' in f['renamed'] %}
    and not exists (
        select 1
        from disputes as d
        where d.fixture_id = b.fixture_id and d.player_id = b.player_id
    )
    {%- endif %}
    except distinct
    select {{ fact_columns }} from {{ ref(f.fact) }} where {{ f.fact_rows }}
) as t
{% if not loop.last %}

union all

{% endif %}
{% endfor %}
