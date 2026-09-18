{#
  The rate guard of engineering_standards.md section 3.2, on the season surface. For every team
  rate the catalogue defines with a denominator, wherever int_team_season__metrics_cumulative
  shows a value at match N, every column its formula reads is present in every non-awarded game
  of that season up to N. Every match number is guarded, not only the latest row: the
  year-over-year model reads mid-season rows.

  Generated from metric_catalogue.csv at run time exactly as assert_form_window_rates_inputs_covered
  is (the inputs are the expression identifiers that are columns of base_relation; no per-rate
  list, no keyword stoplist; availability by base_relation - a team-feed column non-null, a
  player-feed game present at all; awarded results left out).

  Coverage is cumulative, so the season needs no per-row cross join: the first non-awarded match
  whose input is missing is found once per team-season, and every cumulative row from that match
  number on is uncovered. int_team_season_record is one row per game and carries match_number.
#}
{{ config(store_failures = true) }}
-- depends_on: {{ ref('metric_catalogue') }}
-- depends_on: {{ ref('int_team_season__metrics_cumulative') }}
-- depends_on: {{ ref('int_team_season_record') }}
-- depends_on: {{ ref('int_legs__team_match') }}
-- depends_on: {{ ref('int_legs__team_from_players') }}

{% set surface = 'int_team_season__metrics_cumulative' %}
{% set member_floor = 15 %}
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
with first_uncovered as (
    select
        r.team_sk,
        r.league_code,
        r.season_api_year,
        {% for m in members %}
        min(if({{ m.predicate }}, r.match_number, null)) as {{ m.metric }}__first_uncovered{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ ref('int_team_season_record') }} as r
    inner join {{ ref('int_legs__team_match') }} as l
        on r.fixture_sk = l.fixture_sk and r.team_sk = l.team_sk
    left join {{ ref('int_legs__team_from_players') }} as p
        on r.fixture_sk = p.fixture_sk and r.team_sk = p.team_sk
    where not l.is_awarded_result
    group by r.team_sk, r.league_code, r.season_api_year
),

surface as (
    select * from {{ ref(surface) }}
)

{% for m in members %}
select
    '{{ m.metric }}' as metric_id,
    '{{ m.inputs }}' as inputs,
    s.team_sk,
    s.league_code,
    s.season_api_year,
    f.{{ m.metric }}__first_uncovered as first_uncovered_match_number,
    min(s.match_number) as first_shown_match_number,
    count(*) as rows_shown_uncovered
from surface as s
inner join first_uncovered as f
    on s.team_sk = f.team_sk
    and s.league_code = f.league_code
    and s.season_api_year = f.season_api_year
where s.{{ m.metric }} is not null and s.match_number >= f.{{ m.metric }}__first_uncovered
group by 1, 2, 3, 4, 5, 6
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
    cast(null as int64) as team_sk,
    cast(null as string) as league_code,
    cast(null as int64) as season_api_year,
    cast(null as int64) as first_uncovered_match_number,
    cast(null as int64) as first_shown_match_number,
    cast(null as int64) as rows_shown_uncovered
from {{ ref('metric_catalogue') }}
where 1 = 0
{% endif %}
