{#
  Drift guard (metric layer, Phase 1). For each canonical SEASON model, every metric-bearing
  column must be registered in metric_catalogue. The test FAILS (returns rows) if a model
  computes a metric that is not catalogued — i.e. a new metric crept in without being added to
  the layer. This is the no-drift guarantee: the model is the single source, the catalogue is
  the registry, and they cannot silently diverge.

  Non-metric columns are excluded: surrogate / foreign keys (*_sk), the coverage counts, the
  *_sum_season raw intermediates, and the playing-time facts (appearances / starts / subs /
  minutes) which are dimensions, not metrics.

  Naming is normalised to the catalogue's metric_id: #500 Stage 2 has renamed the team-season model
  columns to catalogue-id names (no `_season` suffix), so the strip here is now a defensive no-op;
  it is deliberately NOT a binding-map. (The goals_saves->saves normalisation was removed
  once Stage 1 renamed the player model column to `saves`.) A `team and player` catalogue row
  satisfies both the team and the player model checks.
#}

-- ref()s live inside the execute-guarded loop below, so declare the dependencies explicitly
-- (dbt cannot infer a ref() placed in a conditional; this also orders the test after the models build):
-- depends_on: {{ ref('int_player_season__metrics') }}
-- depends_on: {{ ref('int_player_club_season__metrics') }}
-- depends_on: {{ ref('int_team_season__metrics') }}

{% set models = [
    ('int_player_season__metrics', 'player'),
    ('int_player_club_season__metrics', 'player'),
    ('int_team_season__metrics', 'team')
] %}

{% set exempt = [
    'team_sk', 'player_sk', 'league_sk', 'season_sk', 'league_code', 'season_api_year',
    'season_games_played', 'season_matchdays_used', 'stat_coverage_season_games',
    'player_stat_coverage_season_games', 'games_with_team_stats',
    'games_expecting_team_stats', 'entity_type',
    'appearances', 'starts', 'substitute_appearances', 'minutes', 'last_kickoff_at'
] %}

{% set rows = [] %}
{% if execute %}
    {% for model_name, entity in models %}
        {% for col in adapter.get_columns_in_relation(ref(model_name)) %}
            {% set name = col.name | lower %}
            {% if name not in exempt and not name.endswith('_sum_season') and not name.endswith('_sk') %}
                {% set norm = name[:-7] if name.endswith('_season') else name %}
                {% do rows.append(
                    "select '" ~ entity ~ "' as entity, '" ~ name ~ "' as model_column, '" ~ norm ~ "' as metric_id"
                ) %}
            {% endif %}
        {% endfor %}
    {% endfor %}
{% endif %}

with catalogue as (
    select entity, metric_id from {{ ref('metric_catalogue') }}
),

model_metric_columns as (
    {% if rows %}
    {{ rows | join('\n    union all\n    ') }}
    {% else %}
    select
        cast(null as string) as entity,
        cast(null as string) as model_column,
        cast(null as string) as metric_id
    where 1 = 0
    {% endif %}
)

select
    m.entity,
    m.model_column,
    m.metric_id
from model_metric_columns as m
left join catalogue as c
    on
        m.metric_id = c.metric_id
        and (c.entity = m.entity or c.entity = 'team and player')
where c.metric_id is null
