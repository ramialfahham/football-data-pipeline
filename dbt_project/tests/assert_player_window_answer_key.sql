{#
  Hand-worked window values (seeds/player_window_answer_key.csv): a real player over a whole window
  of the Player page, each value added up by hand from the match lines, by the catalogue formula.
  int_player_window__metrics must return exactly safe_divide(numerator, denominator), or the
  numerator for a value with no denominator. Returns each case whose value differs and each case
  whose metric is not a column of the model or whose player-window is missing.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set columns = [] %}
{% if execute %}
    {% for c in adapter.get_columns_in_relation(ref('int_player_window__metrics')) %}
        {% if c.dtype | upper in ('INT64', 'FLOAT64') %}
            {% do columns.append(c.name | lower) %}
        {% endif %}
    {% endfor %}
    {% if columns | length == 0 %}
        {{ exceptions.raise_compiler_error("int_player_window__metrics has no numeric column: the answer key would compare nothing") }}
    {% endif %}
{% endif %}

with answer_key as (
    select * from {{ ref('player_window_answer_key') }}
),

model as (
    select * from {{ ref('int_player_window__metrics') }}
),

compared as (
    select
        k.player_id,
        k.window_type,
        k.metric_id,
        k.numerator,
        k.denominator,
        k.metric_id in ('{{ columns | join("', '") }}') as on_model,
        m.player_sk is not null as row_found,
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
        on k.player_id = m.player_sk and k.window_type = m.window_type
)

select *
from compared
where
    not on_model
    or not row_found
    or expected_value is distinct from actual_value
