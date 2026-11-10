{#
  The rate guard of engineering_standards.md section 3.2, on the Team page's window surfaces:
  int_team_window__metrics (a club's this season and last season, every club competition) and
  int_team_competition_phase__metrics (an international club competition's league or group phase).
  For every team rate the catalogue defines with a denominator, wherever a surface shows a value,
  every column its formula reads is present in every non-awarded game of that window.

  Generated from metric_catalogue.csv at run time as assert_season_rates_inputs_covered is: the
  inputs are the expression identifiers that are columns of base_relation; a team-feed input is
  present when its leg column is non-null, a player-feed input when the game's player row exists.
  Each window is rebuilt here from the legs, apart from the surface: the club windows anchored at
  the featured season, and the table rounds of an international club competition.
#}
{{ config(store_failures = true) }}
-- depends_on: {{ ref('metric_catalogue') }}
-- depends_on: {{ ref('int_team_window__metrics') }}
-- depends_on: {{ ref('int_team_competition_phase__metrics') }}
-- depends_on: {{ ref('int_legs__team_match') }}
-- depends_on: {{ ref('int_legs__team_from_players') }}
-- depends_on: {{ ref('int_team__featured_season') }}
-- depends_on: {{ ref('int_competition_season__club_windows') }}
-- depends_on: {{ ref('int_round_names') }}
-- depends_on: {{ ref('dim_league') }}

{% set surfaces = ['int_team_window__metrics', 'int_team_competition_phase__metrics'] %}
{% set member_floor = 15 %}
{% set legs = {'int_legs__team_match': 'l', 'int_legs__team_from_players': 'p'} %}
{% set members = [] %}

{% if execute %}
    {% set surface_cols = {} %}
    {% for s in surfaces %}
        {% set cols = [] %}
        {% for c in adapter.get_columns_in_relation(ref(s)) %}
            {% do cols.append(c.name | lower) %}
        {% endfor %}
        {% do surface_cols.update({s: cols}) %}
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
        {% if base in legs and metric in surface_cols[surfaces[0]] and metric in surface_cols[surfaces[1]] %}
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
            "Team page window rate guard built " ~ (members | length) ~ " members (floor " ~ member_floor
            ~ "): the seed read or the surface columns stopped matching, and a guard over nothing passes silently"
        ) }}
    {% endif %}
{% endif %}

{% if members %}
with window_games as (
    select
        'int_team_window__metrics' as surface,
        f.team_sk,
        w.window_type as window_key,
        l.fixture_sk
    from {{ ref('int_team__featured_season') }} as f
    inner join {{ ref('int_competition_season__club_windows') }} as w
        on f.featured_season_sk = w.anchor_season_sk
    inner join {{ ref('int_legs__team_match') }} as l
        on f.team_sk = l.team_sk and w.season_sk = l.season_sk
    union all
    select
        'int_team_competition_phase__metrics' as surface,
        l.team_sk,
        l.season_sk as window_key,
        l.fixture_sk
    from {{ ref('int_legs__team_match') }} as l
    inner join {{ ref('dim_league') }} as c
        on l.league_code = c.league_code
    inner join {{ ref('int_round_names') }} as r
        on
            l.league_code = r.league_code
            and l.season_api_year = r.season_api_year
            and l.round_name = r.round_name
    where
        c.entity_type = 'club'
        and c.competition_type not in ('domestic_league', 'domestic_cup')
        and r.round_stage_kind = 'table'
),

uncovered as (
    select
        g.surface,
        g.team_sk,
        g.window_key,
        {% for m in members %}
        logical_or({{ m.predicate }}) as {{ m.metric }}__uncovered{% if not loop.last %},{% endif %}
        {% endfor %}
    from window_games as g
    inner join {{ ref('int_legs__team_match') }} as l
        on g.fixture_sk = l.fixture_sk and g.team_sk = l.team_sk
    left join {{ ref('int_legs__team_from_players') }} as p
        on g.fixture_sk = p.fixture_sk and g.team_sk = p.team_sk
    where not l.is_awarded_result
    group by g.surface, g.team_sk, g.window_key
),

shown as (
    select
        'int_team_window__metrics' as surface,
        team_sk,
        window_type as window_key,
        {% for m in members %}
        {{ m.metric }}{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ ref('int_team_window__metrics') }}
    union all
    select
        'int_team_competition_phase__metrics' as surface,
        team_sk,
        season_sk as window_key,
        {% for m in members %}
        {{ m.metric }}{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ ref('int_team_competition_phase__metrics') }}
)

{% for m in members %}
select
    s.surface,
    '{{ m.metric }}' as metric_id,
    '{{ m.inputs }}' as inputs,
    s.team_sk,
    s.window_key
from shown as s
inner join uncovered as u
    on s.surface = u.surface and s.team_sk = u.team_sk and s.window_key = u.window_key
where s.{{ m.metric }} is not null and u.{{ m.metric }}__uncovered
{% if not loop.last %}
union all
{% endif %}
{% endfor %}
{% else %}
{# The non-execute render (sqlfluff, dbt compile without a warehouse) - an explicitly empty
   result of the same shape. BigQuery rejects a FROM-less WHERE, hence the seed. #}
select
    cast(null as string) as surface,
    cast(null as string) as metric_id,
    cast(null as string) as inputs,
    cast(null as int64) as team_sk,
    cast(null as string) as window_key
from {{ ref('metric_catalogue') }}
where 1 = 0
{% endif %}
