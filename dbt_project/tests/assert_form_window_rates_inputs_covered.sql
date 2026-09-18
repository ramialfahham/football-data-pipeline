{#
  The rate guard of engineering_standards.md section 3.2, on the form-window surface. For every
  team rate the catalogue defines with a denominator, wherever mart_team_momentum shows a value,
  every column its formula reads is present in every non-awarded leg of that window.

  Generated from metric_catalogue.csv at run time: the identifiers of numerator_expr /
  denominator_expr that are columns of base_relation are the rate's inputs. Every other identifier
  is a keyword by assert_metric_catalogue_expr_resolvable's guarantee, so this test carries no
  per-rate list and no keyword stoplist - a rate added to the catalogue is guarded the moment it
  appears as a column of the surface.

  Availability follows docs/metric_layer.md ("Incomplete data is not calculated"): a team-feed
  input is present when its column is non-null on the leg; a player-feed input is present when
  int_legs__team_from_players has the game at all, because a blank player stat is a zero. Player-
  entity metrics are outside the guard by that same rule. Awarded results (AWD / WO) never count
  against coverage and are left out of the legs.

  The member floor: `metric in surface_cols` skips a rate silently when its surface column is
  renamed, so a guard that shrank to nothing would pass. Below the floor the build fails loudly.
#}
{{ config(store_failures = true) }}
-- depends_on: {{ ref('metric_catalogue') }}
-- depends_on: {{ ref('mart_team_momentum') }}
-- depends_on: {{ ref('int_team_momentum_window') }}
-- depends_on: {{ ref('int_legs__team_match') }}
-- depends_on: {{ ref('int_legs__team_from_players') }}

{% set surface = 'mart_team_momentum' %}
{% set member_floor = 10 %}
{% set legs = {'int_legs__team_match': 'l', 'int_legs__team_from_players': 'p'} %}
{% set members = [] %}

{% if execute %}
    {% set surface_cols = [] %}
    {% for c in adapter.get_columns_in_relation(ref(surface)) %}
        {% do surface_cols.append(c.name | lower) %}
    {% endfor %}
    {% set base_cols = {} %}
    {% for rel in legs %}
        {% set cols = [] %}
        {% for c in adapter.get_columns_in_relation(ref(rel)) %}
            {% do cols.append(c.name | lower) %}
        {% endfor %}
        {% do base_cols.update({rel: cols}) %}
    {% endfor %}

    {% set seed = run_query(
        "select metric_id, base_relation, numerator_expr, denominator_expr from " ~ ref('metric_catalogue')
        ~ " where entity in ('team', 'team and player') and computation_kind = 'expression'"
        ~ " and coalesce(trim(denominator_expr), '') != '' order by metric_id"
    ) %}
    {% for row in seed.rows %}
        {% set metric = (row[0] | string | trim | lower) %}
        {% set base = (row[1] | string | trim) if row[1] is not none else '' %}
        {% if metric in surface_cols and base in legs %}
            {% set inputs = [] %}
            {% for expr in [row[2], row[3]] %}
                {% set cleaned = modules.re.sub("'[^']*'", ' ', expr | string) %}
                {% for tok in modules.re.findall('[a-zA-Z_][a-zA-Z0-9_]*', cleaned) %}
                    {% set t = tok | lower %}
                    {% if t in base_cols[base] and t not in inputs %}
                        {% do inputs.append(t) %}
                    {% endif %}
                {% endfor %}
            {% endfor %}
            {% if base == 'int_legs__team_from_players' %}
                {% set predicate = 'p.fixture_sk is null' %}
            {% else %}
                {% set preds = [] %}
                {% for t in inputs %}
                    {% do preds.append('l.' ~ t ~ ' is null') %}
                {% endfor %}
                {% set predicate = preds | join(' or ') %}
            {% endif %}
            {% do members.append({'metric': metric, 'predicate': predicate, 'inputs': inputs | join(' ')}) %}
        {% endif %}
    {% endfor %}

    {% if members | length < member_floor %}
        {{ exceptions.raise_compiler_error(
            surface ~ " rate guard built " ~ (members | length) ~ " members (floor " ~ member_floor
            ~ "): the seed read or the surface columns stopped matching, and a guard over nothing passes silently"
        ) }}
    {% endif %}
{% endif %}

{% if members %}
with uncovered as (
    select
        w.upcoming_fixture_sk,
        w.team_sk,
        {% for m in members %}
        countif({{ m.predicate }}) as {{ m.metric }}__uncovered{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ ref('int_team_momentum_window') }} as w
    left join {{ ref('int_legs__team_match') }} as l
        on w.leg_fixture_sk = l.fixture_sk and w.team_sk = l.team_sk
    left join {{ ref('int_legs__team_from_players') }} as p
        on w.leg_fixture_sk = p.fixture_sk and w.team_sk = p.team_sk
    where not w.is_awarded_result
    group by w.upcoming_fixture_sk, w.team_sk
),

surface as (
    select * from {{ ref(surface) }}
)

{% for m in members %}
select
    '{{ m.metric }}' as metric_id,
    '{{ m.inputs }}' as inputs,
    s.upcoming_fixture_sk,
    s.team_sk,
    s.window_type,
    s.games_expecting_team_stats,
    u.{{ m.metric }}__uncovered as uncovered_games,
    cast(s.{{ m.metric }} as float64) as shown_value
from surface as s
inner join uncovered as u
    on s.upcoming_fixture_sk = u.upcoming_fixture_sk and s.team_sk = u.team_sk
where s.{{ m.metric }} is not null and u.{{ m.metric }}__uncovered > 0
{% if not loop.last %}
union all
{% endif %}
{% endfor %}
{% else %}
{# The non-execute render (sqlfluff, dbt compile without a warehouse) - an explicitly empty
   result of the same shape. BigQuery rejects a FROM-less WHERE, hence the seed. #}
select
    cast(null as string) as metric_id,
    cast(null as string) as inputs,
    cast(null as int64) as upcoming_fixture_sk,
    cast(null as int64) as team_sk,
    cast(null as string) as window_type,
    cast(null as int64) as games_expecting_team_stats,
    cast(null as int64) as uncovered_games,
    cast(null as float64) as shown_value
from {{ ref('metric_catalogue') }}
where 1 = 0
{% endif %}
