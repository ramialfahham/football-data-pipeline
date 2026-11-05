{#
  The player competition-benchmark metrics in LONG form, per player-season and position: one row
  per (player_sk, season_sk, position_group, metric_key) where the player enters the benchmark, with
  the value and, for a ratio metric, the numerator and denominator behind it.
  int_player_competition_benchmarks aggregates it to the positional distribution and
  mart_player_competition_benchmarks ranks each player against it, so the two cannot drift apart.
  Who enters is the ranking_rules doc block in models/docs/metric_rules.md; its floors are the vars
  player_min_minutes and player_min_shots_on_target. The metrics and their positions are the macro
  player_benchmark_metrics.
  Grain: (player_sk, season_sk, position_group, metric_key).
#}

with season as (
    select * from {{ ref('int_player_season_position__metrics') }}
    where minutes >= {{ var('player_min_minutes') }}
)

select
    s.player_sk,
    s.season_sk,
    s.league_sk,
    s.league_code,
    s.season_api_year,
    s.position_group,
    s.minutes,
    s.appearances,
    m.metric_key,
    m.metric_value,
    m.metric_numerator,
    m.metric_denominator
from season as s,
    unnest({{ player_benchmark_metrics('s') }}) as m
where
    s.position_group in unnest(m.position_groups)
    and m.is_qualified
    and m.metric_value is not null
