{#
  Hand-worked season values (seeds/player_season_answer_key.csv): real player-seasons, each
  catalogue metric's numerator and denominator worked out by hand from the provider's raw match
  data, by the catalogue formula and the cleaning rules. int_player_season__metrics must return
  exactly safe_divide(numerator, denominator), or the numerator for a metric with no denominator; a
  blank numerator means the value must be blank. Returns each case whose value differs, whose metric
  is not a player metric of the catalogue or not a column of the model, and whose player-season is
  missing.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set columns = [] %}
{% if execute %}
    {% for c in adapter.get_columns_in_relation(ref('int_player_season__metrics')) %}
        {% if c.dtype | upper in ('INT64', 'FLOAT64') %}
            {% do columns.append(c.name | lower) %}
        {% endif %}
    {% endfor %}
    {% if columns | length == 0 %}
        {{ exceptions.raise_compiler_error("int_player_season__metrics has no numeric column: the answer key would compare nothing") }}
    {% endif %}
{% endif %}

with answer_key as (
    select * from {{ ref('player_season_answer_key') }}
),

catalogue as (
    select
        metric_id,
        denominator_expr
    from {{ ref('metric_catalogue') }}
    where entity = 'player'
),

model as (
    select * from {{ ref('int_player_season__metrics') }}
),

compared as (
    select
        k.league_code,
        k.season,
        k.player_id,
        k.metric_id,
        k.numerator,
        k.denominator,
        c.metric_id is not null as in_catalogue,
        k.metric_id in ('{{ columns | join("', '") }}') as on_model,
        m.player_sk is not null as row_found,
        case
            when k.numerator is null then null
            when c.denominator_expr is not null then safe_divide(k.numerator, k.denominator)
            else cast(k.numerator as float64)
        end as expected_value,
        case k.metric_id
            {% for col in columns %}
            when '{{ col }}' then cast(m.{{ col }} as float64)
            {% endfor %}
        end as actual_value
    from answer_key as k
    left join catalogue as c
        on k.metric_id = c.metric_id
    left join model as m
        on k.league_code = m.league_code and k.season = m.season_api_year and k.player_id = m.player_sk
)

select *
from compared
where
    not in_catalogue
    or not on_model
    or not row_found
    or expected_value is distinct from actual_value
