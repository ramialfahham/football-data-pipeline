{% macro team_benchmark_metrics() %}
{#
  The 20 team season metrics the competition benchmark covers, as (metric_key, season_column) pairs.
  metric_key is the metric_catalogue id; season_column is the column in
  int_team_season__metrics. Single source so the benchmark intermediate (the league
  distribution) and the mart (per-team value + rank) cannot drift apart. Excludes shot_share +
  points_capture (deserved-vs-actual inputs, structurally fixed league means), league_rank + points_won
  (non-metrics), and dribbles_success_pct (retired team-side, #510).
#}
    {% set metrics = [
        ('goals_per_match', 'goals_per_match'),
        ('goals_against_per_match', 'goals_against_per_match'),
        ('clean_sheets', 'clean_sheets'),
        ('shots_per_match', 'shots_per_match'),
        ('shot_accuracy', 'shot_accuracy'),
        ('danger_zone_ratio', 'danger_zone_ratio'),
        ('shots_on_goal_per_match', 'shots_on_goal_per_match'),
        ('finishing_efficiency', 'finishing_efficiency'),
        ('duels_per_match', 'duels_per_match'),
        ('duels_won_pct', 'duels_won_pct'),
        ('defensive_actions_per_match', 'defensive_actions_per_match'),
        ('tackles_per_match', 'tackles_per_match'),
        ('interceptions_per_match', 'interceptions_per_match'),
        ('blocks_per_match', 'blocks_per_match'),
        ('passes_per_match', 'passes_per_match'),
        ('pass_accuracy', 'pass_accuracy'),
        ('key_passes_per_match', 'key_passes_per_match'),
        ('corner_kicks_per_match', 'corner_kicks_per_match'),
        ('corners_against_per_match', 'corners_against_per_match'),
        ('save_ratio', 'save_ratio')
    ] %}
    {{ return(metrics) }}
{% endmacro %}
