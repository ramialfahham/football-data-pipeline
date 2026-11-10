{#
  Hand-worked window values (seeds/team_window_answer_key.csv): a real club over a whole window of
  the Team page, each value added up by hand from the match lines, by the catalogue formula.
  int_team_window__metrics must return exactly safe_divide(numerator, denominator), or the
  numerator for a value with no denominator. A case holds while the club's featured season is the
  one it was worked for (anchor_league_code, anchor_season_api_year); once the club moves on, the
  window covers other matches and the case checks nothing. Returns each case whose team-window is
  missing, and, while the case holds, each whose value differs or whose metric is not a column of
  the model.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set columns = [] %}
{% if execute %}
    {% for c in adapter.get_columns_in_relation(ref('int_team_window__metrics')) %}
        {% if c.dtype | upper in ('INT64', 'FLOAT64') %}
            {% do columns.append(c.name | lower) %}
        {% endif %}
    {% endfor %}
    {% if columns | length == 0 %}
        {{ exceptions.raise_compiler_error("int_team_window__metrics has no numeric column: the answer key would compare nothing") }}
    {% endif %}
{% endif %}

with answer_key as (
    select * from {{ ref('team_window_answer_key') }}
),

model as (
    select * from {{ ref('int_team_window__metrics') }}
),

anchors as (
    select
        season_sk,
        league_code,
        season_api_year
    from {{ ref('dim_competition_season') }}
),

compared as (
    select
        k.team_id,
        k.window_type,
        k.metric_id,
        k.numerator,
        k.denominator,
        k.metric_id in ('{{ columns | join("', '") }}') as on_model,
        m.team_sk is not null as row_found,
        a.season_sk is not null as case_holds,
        if(
            k.denominator is null,
            cast(k.numerator as float64),
            safe_divide(k.numerator, k.denominator)
        ) as expected_value,
        case k.metric_id
            {% for col in columns %}
            when '{{ col }}' then cast(m.{{ col }} as float64)
            {% endfor %}
        end as actual_value
    from answer_key as k
    left join model as m
        on k.team_id = m.team_sk and k.window_type = m.window_type
    left join anchors as a
        on
            m.anchor_season_sk = a.season_sk
            and k.anchor_league_code = a.league_code
            and k.anchor_season_api_year = a.season_api_year
)

select *
from compared
where
    not row_found
    or (case_holds and not on_model)
    or (case_holds and expected_value is distinct from actual_value)
