{#
  Every team metric a surface computes equals its metric_catalogue formula, recomputed here from
  int_legs__team_match and int_legs__team_from_players over the surface's own window, under the
  rules in models/docs/metric_rules.md. The formula is read from the seed at run time, so a surface
  that drifts from the catalogue, or a catalogue change the surfaces did not follow, fails here.
  Floats compare at a relative 1e-9.

  One row per disagreeing value (surface, metric, grain, model value, expected value), plus one per
  grain present on one side only. The match-stats mart carries the pass accuracy of the team's own
  match as a whole percentage (passes_accuracy_percent), checked the same way.
#}
{{ config(store_failures = true, severity = 'error') }}
-- depends_on: {{ ref('metric_catalogue') }}
-- depends_on: {{ ref('int_legs__team_match') }}
-- depends_on: {{ ref('int_legs__team_from_players') }}
-- depends_on: {{ ref('int_team_momentum_window') }}
-- depends_on: {{ ref('int_team_season__metrics_cumulative') }}
-- depends_on: {{ ref('int_team_season__metrics') }}
-- depends_on: {{ ref('int_team_momentum__metrics') }}
-- depends_on: {{ ref('mart_team_momentum') }}
-- depends_on: {{ ref('mart_team_fixture_stats') }}
-- depends_on: {{ ref('fct_fixture_team_stats') }}

{% set surfaces = [
    {'model': 'int_team_season__metrics_cumulative', 'rows': 'season_rows',
     'grain': ['team_sk', 'league_code', 'season_api_year', 'match_number'], 'windowed': true},
    {'model': 'int_team_season__metrics', 'rows': 'season_rows',
     'grain': ['team_sk', 'season_sk'], 'windowed': false},
    {'model': 'int_team_momentum__metrics', 'rows': 'momentum_rows',
     'grain': ['upcoming_fixture_sk', 'team_sk'], 'windowed': false},
    {'model': 'mart_team_momentum', 'rows': 'momentum_rows',
     'grain': ['upcoming_fixture_sk', 'team_sk'], 'windowed': false},
] %}
{% set forfeit_counted = ['points_won', 'goals', 'goals_against'] %}
{% set member_floor = 100 %}
{% set checks = [] %}

{% if execute %}
    {% set seed = run_query(
        "select metric_id, numerator_expr, denominator_expr from " ~ ref('metric_catalogue')
        ~ " where entity = 'team' and computation_kind = 'expression'"
        ~ " and base_relation in ('int_legs__team_match', 'int_legs__team_from_players') order by metric_id"
    ) %}
    {% for s in surfaces %}
        {% set columns = [] %}
        {% for c in adapter.get_columns_in_relation(ref(s.model)) %}
            {% do columns.append(c.name | lower) %}
        {% endfor %}
        {% set over = ' over w' if s.windowed else '' %}
        {% set metrics = [] %}
        {% for row in seed.rows %}
            {% set metric = row[0] | string | trim | lower %}
            {% if metric in columns %}
                {% set counted = 'true' if metric in forfeit_counted else 'not is_awarded_result' %}
                {% set parts = [] %}
                {% for expr in [row[1], row[2]] %}
                    {% set e = (expr | string | trim) if expr is not none else '' %}
                    {% if e %}
                        {% set gated = modules.re.sub(
                            '\\b(sum|countif)\\(([^()]*)\\)',
                            'case when countif(' ~ counted ~ ' and (\\2) is null)' ~ over
                            ~ ' > 0 then null else \\1(case when ' ~ counted ~ ' then \\2 end)' ~ over ~ ' end',
                            e | replace('count(*)', '__matches__')
                        ) %}
                        {% do parts.append(gated | replace('__matches__', 'countif(' ~ counted ~ ')' ~ over)) %}
                    {% endif %}
                {% endfor %}
                {% set expected = parts[0] if parts | length == 1 else 'safe_divide(' ~ parts[0] ~ ', ' ~ parts[1] ~ ')' %}
                {% do metrics.append({'metric': metric, 'expected': expected}) %}
            {% endif %}
        {% endfor %}
        {% do checks.append({'surface': s, 'metrics': metrics}) %}
    {% endfor %}
    {% set total = checks | map(attribute='metrics') | map('length') | sum %}
    {% if total < member_floor %}
        {{ exceptions.raise_compiler_error(
            "the formula recompute built " ~ total ~ " surface metrics (floor " ~ member_floor
            ~ "): the seed read or the surface columns stopped matching, and a check over nothing passes silently"
        ) }}
    {% endif %}
{% endif %}

with legs as (
    select
        tm.*,
        tp.passes_key,
        tp.tackles,
        tp.interceptions,
        tp.blocks,
        tp.duels,
        tp.duels_won,
        tp.dribbles,
        tp.dribbles_success
    from {{ ref('int_legs__team_match') }} as tm
    left join {{ ref('int_legs__team_from_players') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
),

season_rows as (
    select
        *,
        row_number() over (
            partition by team_sk, league_code, season_api_year
            order by kickoff_datetime asc, fixture_sk asc
        ) as match_number
    from legs
),

momentum_rows as (
    select
        w.upcoming_fixture_sk,
        legs.*
    from {{ ref('int_team_momentum_window') }} as w
    inner join legs
        on w.leg_fixture_sk = legs.fixture_sk and w.team_sk = legs.team_sk
),

{% for check in checks %}
{% set s = check.surface %}
{{ s.model }}__expected as (
    select
        {% for key in s.grain %}{{ key }},{% endfor %}
        {% for m in check.metrics %}
        {{ m.expected }} as {{ m.metric }}{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ s.rows }}
    {% if s.windowed %}
    window w as (
        partition by team_sk, league_code, season_api_year
        order by kickoff_datetime asc, fixture_sk asc
        rows between unbounded preceding and current row
    )
    {% else %}
    group by {{ s.grain | join(', ') }}
    {% endif %}
),

{{ s.model }}__compared as (
    select
        '{{ s.model }}' as surface,
        to_json_string(struct(
            {% for key in s.grain %}coalesce(e.{{ key }}, m.{{ key }}) as {{ key }}{% if not loop.last %}, {% endif %}{% endfor %}
        )) as grain,
        m.{{ s.grain[0] }} is not null as in_model,
        e.{{ s.grain[0] }} is not null as in_expected,
        [
            {% for m in check.metrics %}
            struct(
                '{{ m.metric }}' as metric_id,
                cast(m.{{ m.metric }} as float64) as model_value,
                cast(e.{{ m.metric }} as float64) as expected_value
            ){% if not loop.last %},{% endif %}
            {% endfor %}
        ] as metric_values
    from {{ s.model }}__expected as e
    full outer join {{ ref(s.model) }} as m
        on {% for key in s.grain %}e.{{ key }} = m.{{ key }}{% if not loop.last %} and {% endif %}{% endfor %}
),
{% endfor %}

match_level as (
    select
        m.fixture_sk,
        m.team_sk,
        m.passes_accuracy_percent as mart_value,
        cast(round(100 * safe_divide(s.passes_accurate, s.passes)) as int64) as expected_percent
    from {{ ref('mart_team_fixture_stats') }} as m
    inner join {{ ref('fct_fixture_team_stats') }} as s
        on m.fixture_sk = s.fixture_sk and m.team_sk = s.team_sk
)

{% for check in checks %}
select
    surface,
    if(in_model and in_expected, v.metric_id, 'grain on one side only') as metric_id,
    grain,
    v.model_value,
    v.expected_value
from {{ check.surface.model }}__compared, unnest(metric_values) as v
where
    not (in_model and in_expected)
    or (v.model_value is null) != (v.expected_value is null)
    or abs(v.model_value - v.expected_value) > 1e-9 * greatest(1, abs(v.expected_value))

union all
{% endfor %}

select
    'mart_team_fixture_stats' as surface,
    'passes_accuracy_percent' as metric_id,
    to_json_string(struct(fixture_sk, team_sk)) as grain,
    cast(mart_value as float64) as model_value,
    cast(expected_percent as float64) as expected_value
from match_level
where mart_value is distinct from expected_percent
