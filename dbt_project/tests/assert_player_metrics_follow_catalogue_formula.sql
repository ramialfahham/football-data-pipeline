{#
  Every player metric a surface computes equals its metric_catalogue formula, recomputed here from
  int_legs__player_match over the surface's own window, under the rules in
  models/docs/metric_rules.md. The formula is read from the seed at run time, so a surface that
  drifts from the catalogue, or a catalogue change the surfaces did not follow, fails here. Floats
  compare at a relative 1e-9.

  One row per disagreeing value (surface, metric, grain, model value, expected value), plus one per
  grain present on one side only. The two match-level marts carry the pass accuracy of the player's
  own match as a whole percentage (passes_accuracy_percent), checked the same way.
#}
{{ config(store_failures = true, severity = 'error') }}
-- depends_on: {{ ref('metric_catalogue') }}
-- depends_on: {{ ref('int_legs__player_match') }}
-- depends_on: {{ ref('int_legs__team_match') }}
-- depends_on: {{ ref('int_legs__team_from_players') }}
-- depends_on: {{ ref('int_team_momentum_window') }}
-- depends_on: {{ ref('int_player_club_season__metrics') }}
-- depends_on: {{ ref('int_player_season__metrics') }}
-- depends_on: {{ ref('int_player_season_position__metrics') }}
-- depends_on: {{ ref('int_player_momentum__metrics') }}
-- depends_on: {{ ref('int_player_season_record') }}
-- depends_on: {{ ref('int_player_profile__contribution') }}
-- depends_on: {{ ref('mart_player_fixture_stats') }}
-- depends_on: {{ ref('mart_player_match_log') }}
-- depends_on: {{ ref('fct_fixture_player_stats') }}

{% set surfaces = [
    {'model': 'int_player_club_season__metrics', 'rows': 'club_season_rows',
     'grain': ['player_sk', 'team_sk', 'season_sk'], 'windowed': false},
    {'model': 'int_player_season__metrics', 'rows': 'season_rows',
     'grain': ['player_sk', 'season_sk'], 'windowed': false},
    {'model': 'int_player_season_position__metrics', 'rows': 'position_rows',
     'grain': ['player_sk', 'season_sk', 'position_group'], 'windowed': false},
    {'model': 'int_player_momentum__metrics', 'rows': 'momentum_rows',
     'grain': ['upcoming_fixture_sk', 'team_sk', 'player_sk'], 'windowed': false},
    {'model': 'int_player_season_record', 'rows': 'record_rows',
     'grain': ['team_sk', 'player_sk', 'league_code', 'season_api_year', 'fixture_sk'], 'windowed': true},
    {'model': 'int_player_profile__contribution', 'rows': 'contribution_rows',
     'grain': ['player_sk', 'team_sk', 'season_sk'], 'windowed': false},
] %}
{% set member_floor = 60 %}
{% set checks = [] %}

{% if execute %}
    {% set seed = run_query(
        "select metric_id, numerator_expr, denominator_expr from " ~ ref('metric_catalogue')
        ~ " where entity = 'player' and computation_kind = 'expression'"
        ~ " and base_relation = 'int_legs__player_match' order by metric_id"
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
                {% set parts = [] %}
                {% for expr in [row[1], row[2]] %}
                    {% set e = (expr | string | trim) if expr is not none else '' %}
                    {% if e %}
                        {% do parts.append(modules.re.sub(
                            '\\b(sum|countif)\\(([^()]*)\\)',
                            'case when countif(not window_is_complete or (\\2) is null)' ~ over
                            ~ ' > 0 then null else \\1(\\2)' ~ over ~ ' end',
                            e
                        )) %}
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
    select * from {{ ref('int_legs__player_match') }}
),

team_matches_without_player_data as (
    select
        tm.fixture_sk,
        tm.team_sk,
        tm.season_sk,
        tm.league_code,
        tm.season_api_year,
        tm.kickoff_datetime
    from {{ ref('int_legs__team_match') }} as tm
    left join {{ ref('int_legs__team_from_players') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
    where not tm.is_awarded_result and tp.fixture_sk is null
),

club_season_rows as (
    select
        legs.*,
        not exists (
            select 1 from team_matches_without_player_data as u
            where u.team_sk = legs.team_sk and u.season_sk = legs.season_sk
        ) as window_is_complete
    from legs
),

season_rows as (
    select
        * except (window_is_complete),
        logical_and(window_is_complete) over (partition by player_sk, season_sk) as window_is_complete
    from club_season_rows
),

position_rows as (
    select
        *,
        case position_code when 'G' then 'GK' when 'D' then 'DEF' when 'M' then 'MID' when 'F' then 'ATT' end
            as position_group
    from season_rows
    where position_code in ('G', 'D', 'M', 'F')
),

momentum_rows as (
    select
        w.upcoming_fixture_sk,
        legs.* except (team_sk),
        w.team_sk,
        not exists (
            select 1
            from {{ ref('int_team_momentum_window') }} as w2
            inner join team_matches_without_player_data as u
                on w2.leg_fixture_sk = u.fixture_sk and w2.team_sk = u.team_sk
            where w2.upcoming_fixture_sk = w.upcoming_fixture_sk and w2.team_sk = w.team_sk
        ) as window_is_complete
    from {{ ref('int_team_momentum_window') }} as w
    inner join legs
        on w.leg_fixture_sk = legs.fixture_sk and w.team_sk = legs.team_sk
),

record_rows as (
    select
        legs.*,
        not exists (
            select 1 from team_matches_without_player_data as u
            where
                u.team_sk = legs.team_sk and u.league_code = legs.league_code
                and u.season_api_year = legs.season_api_year and u.kickoff_datetime <= legs.kickoff_datetime
        ) as window_is_complete
    from legs
    where legs.minutes > 0 or legs.minutes is null
),

contribution_rows as (
    select
        legs.* except (season_sk),
        tm.season_sk,
        not exists (
            select 1 from team_matches_without_player_data as u
            where u.team_sk = legs.team_sk and u.season_sk = tm.season_sk
        ) as window_is_complete
    from legs
    inner join {{ ref('int_legs__team_match') }} as tm
        on legs.fixture_sk = tm.fixture_sk and legs.team_sk = tm.team_sk
),

{% for check in checks %}
{% set s = check.surface %}
{{ s.model }}__expected as (
    select
        {% for key in s.grain %}{{ key }},{% endfor %}
        {% if s.windowed %}minutes,{% endif %}
        {% for m in check.metrics %}
        {{ m.expected }} as {{ m.metric }}{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ s.rows }}
    {% if s.windowed %}
    window w as (
        partition by team_sk, player_sk, league_code, season_api_year
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
    from (
        select * from {{ s.model }}__expected
        {% if s.windowed %}where minutes > 0{% endif %}
    ) as e
    full outer join {{ ref(s.model) }} as m
        on {% for key in s.grain %}e.{{ key }} = m.{{ key }}{% if not loop.last %} and {% endif %}{% endfor %}
),
{% endfor %}

match_level as (
    select
        s.fixture_sk,
        s.team_sk,
        s.player_sk,
        cast(round(100 * safe_divide(s.passes_accurate, s.passes)) as int64) as expected_percent,
        fs.passes_accuracy_percent as fixture_stats_percent,
        ml.passes_accuracy_percent as match_log_percent,
        fs.fixture_sk is not null as in_fixture_stats,
        ml.fixture_sk is not null as in_match_log
    from {{ ref('fct_fixture_player_stats') }} as s
    inner join {{ ref('int_legs__player_match') }} as l
        on s.fixture_sk = l.fixture_sk and s.player_sk = l.player_sk
    left join {{ ref('mart_player_fixture_stats') }} as fs
        on s.fixture_sk = fs.fixture_sk and s.team_sk = fs.team_sk and s.player_sk = fs.player_sk
    left join {{ ref('mart_player_match_log') }} as ml
        on s.fixture_sk = ml.fixture_sk and s.player_sk = ml.player_sk
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
    mart as surface,
    'passes_accuracy_percent' as metric_id,
    to_json_string(struct(fixture_sk, team_sk, player_sk)) as grain,
    cast(mart_value as float64) as model_value,
    cast(expected_percent as float64) as expected_value
from match_level,
    unnest([
        struct('mart_player_fixture_stats' as mart, fixture_stats_percent as mart_value, in_fixture_stats as present),
        struct('mart_player_match_log', match_log_percent, in_match_log)
    ])
where present and mart_value is distinct from expected_percent
