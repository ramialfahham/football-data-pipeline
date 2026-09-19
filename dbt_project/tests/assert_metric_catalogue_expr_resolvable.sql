{#
  Resolvability guard (#530 PR2). Every column identifier in a metric's numerator_expr /
  denominator_expr must be a real column of its base_relation — otherwise the formula cannot be
  computed from that building block. The test FAILS (returns rows) for any expr token that is
  neither a SQL keyword/function (the stoplist) nor a column of the row's base_relation.

  Rows with a blank base_relation are skipped (the lookup and fitted / rank-derived metrics —
  league_rank / deserved_points / deserved_rank / deserved_points_gap — and the deferred entity-dual rows
  have no leg formula to resolve). The skip keys on base_relation being blank, never on these names,
  so the list is documentation and adding one does not require touching this test. Quoted string
  literals (e.g. result = 'W') are stripped before tokenizing; numeric literals never match the
  identifier regex.

  Mirrors assert_no_uncatalogued_season_metric: the ref()s live in the execute-guarded block, so the
  dependencies are declared explicitly to order the test after the seed + leg models build.
#}
{{ config(store_failures = true) }}
-- depends_on: {{ ref('metric_catalogue') }}
-- depends_on: {{ ref('int_legs__team_match') }}
-- depends_on: {{ ref('int_legs__team_from_players') }}
-- depends_on: {{ ref('int_legs__player_match') }}

{% set base_relations = ['int_legs__team_match', 'int_legs__team_from_players', 'int_legs__player_match'] %}

{# SQL keywords / functions / cast types that appear in formulas and are NOT columns. The 12 the
   current catalogue uses, plus a small defensive set. A new function in a future formula fails here
   until added to this list — an intentional, explicit signal, not a silent pass. #}
{% set sql_tokens = [
    'as', 'case', 'cast', 'count', 'countif', 'else', 'end', 'int64', 'round', 'sum', 'then', 'when',
    'and', 'or', 'not', 'null', 'is', 'coalesce', 'safe_divide', 'nullif'
] %}

{% set bad_rows = [] %}
{% if execute %}
    {# column set per base relation #}
    {% set base_cols = {} %}
    {% for rel in base_relations %}
        {% set cols = [] %}
        {% for c in adapter.get_columns_in_relation(ref(rel)) %}
            {% do cols.append(c.name | lower) %}
        {% endfor %}
        {% do base_cols.update({rel: cols}) %}
    {% endfor %}

    {% set seed = run_query('select metric_id, entity, base_relation, numerator_expr, denominator_expr from ' ~ ref('metric_catalogue')) %}
    {% for row in seed.rows %}
        {% set base = (row[2] | string | trim) if row[2] is not none else '' %}
        {% if base in base_cols %}
            {% for expr in [row[3], row[4]] %}
                {% set e = (expr | string | trim) if expr is not none else '' %}
                {% if e %}
                    {% set cleaned = modules.re.sub("'[^']*'", ' ', e) %}
                    {% for tok in modules.re.findall('[a-zA-Z_][a-zA-Z0-9_]*', cleaned) %}
                        {% set t = tok | lower %}
                        {% if t not in sql_tokens and t not in base_cols[base] %}
                            {% do bad_rows.append(
                                "select '" ~ row[0] ~ "' as metric_id, '" ~ row[1] ~ "' as entity, '" ~ base ~ "' as base_relation, '" ~ t ~ "' as unresolved_token"
                            ) %}
                        {% endif %}
                    {% endfor %}
                {% endif %}
            {% endfor %}
        {% endif %}
    {% endfor %}
{% endif %}

{% if bad_rows %}
{{ bad_rows | join('\nunion all\n') }}
{% else %}
{# No unresolved tokens — emit an explicitly-empty result. BigQuery rejects a FROM-less WHERE,
   so select from the seed (already a dependency) with a false predicate to yield zero rows. #}
select
    cast(null as string) as metric_id,
    cast(null as string) as entity,
    cast(null as string) as base_relation,
    cast(null as string) as unresolved_token
from {{ ref('metric_catalogue') }}
where 1 = 0
{% endif %}
