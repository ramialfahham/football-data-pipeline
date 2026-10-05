{#
  The 18 player competition-benchmark metrics in LONG form, per player-season and position: one row
  per (player_sk, season_sk, position_group, metric_key) where the player enters the benchmark, with
  the value and, for the 5 ratio metrics, the numerator and denominator behind it. The single source
  of the benchmark metric set and of the positions each metric is benchmarked for:
  int_player_competition_benchmarks aggregates it to the positional distribution and
  mart_player_competition_benchmarks ranks each player against it, so the two cannot drift apart.
  Who enters is the ranking_rules doc block in models/docs/metric_rules.md; its floors are the vars
  player_min_minutes and player_min_shots_on_target. A metric is benchmarked for goalkeepers on
  saves and passing and for outfield players on every metric but saves.
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
    unnest([
        struct(
            'saves_per90' as metric_key,
            ['GK'] as position_groups,
            true as is_qualified,
            s.saves_per90 as metric_value,
            cast(null as int64) as metric_numerator,
            cast(null as int64) as metric_denominator
        ),
        (
            'saves_player_pct', ['GK'], true, s.saves_player_pct,
            s.saves_player, s.saves_player + s.goals_against_player
        ),
        ('passes_per90', ['GK', 'DEF', 'MID', 'ATT'], true, s.passes_per90, null, null),
        (
            'passes_accuracy_player_pct', ['GK', 'DEF', 'MID', 'ATT'], true, s.passes_accuracy_player_pct,
            s.passes_accurate_player, s.passes_player
        ),
        ('goals_per90', ['DEF', 'MID', 'ATT'], true, s.goals_per90, null, null),
        ('assists_per90', ['DEF', 'MID', 'ATT'], true, s.assists_per90, null, null),
        ('scorer_points_per90', ['DEF', 'MID', 'ATT'], true, s.scorer_points_per90, null, null),
        ('shots_on_goal_per90', ['DEF', 'MID', 'ATT'], true, s.shots_on_goal_per90, null, null),
        ('passes_key_per90', ['DEF', 'MID', 'ATT'], true, s.passes_key_per90, null, null),
        (
            'finishing_efficiency_player_pct', ['DEF', 'MID', 'ATT'],
            s.shots_on_goal_player >= {{ var('player_min_shots_on_target') }},
            s.finishing_efficiency_player_pct,
            s.goals_player - s.goals_penalty_player, s.shots_on_goal_player
        ),
        ('dribbles_success_per90', ['DEF', 'MID', 'ATT'], true, s.dribbles_success_per90, null, null),
        (
            'dribbles_success_player_pct', ['DEF', 'MID', 'ATT'], true, s.dribbles_success_player_pct,
            s.dribbles_success_player, s.dribbles_attempts_player
        ),
        ('duels_won_per90', ['DEF', 'MID', 'ATT'], true, s.duels_won_per90, null, null),
        (
            'duels_won_player_pct', ['DEF', 'MID', 'ATT'], true, s.duels_won_player_pct,
            s.duels_won_player, s.duels_player
        ),
        ('defensive_actions_per90', ['DEF', 'MID', 'ATT'], true, s.defensive_actions_per90, null, null),
        ('tackles_per90', ['DEF', 'MID', 'ATT'], true, s.tackles_per90, null, null),
        ('interceptions_per90', ['DEF', 'MID', 'ATT'], true, s.interceptions_per90, null, null),
        ('blocks_per90', ['DEF', 'MID', 'ATT'], true, s.blocks_per90, null, null)
    ]) as m
where
    s.position_group in unnest(m.position_groups)
    and m.is_qualified
    and m.metric_value is not null
