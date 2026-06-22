{% macro team_benchmark_metrics() %}
{#
  The 20 team season metrics the competition benchmark covers, as (metric_key, season_column) pairs.
  metric_key is the metric_catalogue id; season_column is the column in
  int_team_season__full_season_metrics. Single source so the benchmark intermediate (the league
  distribution) and the mart (per-team value + rank) cannot drift apart. Excludes shot_share +
  points_capture (deserved-vs-actual inputs, structurally fixed league means), league_rank + points_won
  (non-metrics), and dribbles_success_pct (retired team-side, #510).
#}
    {% set metrics = [
        ('goals_per_match', 'goals_per_match_season'),
        ('goals_against_per_match', 'goals_against_per_match_season'),
        ('clean_sheets', 'clean_sheets_season'),
        ('shots_per_match', 'shots_per_match_season'),
        ('shot_accuracy', 'shot_accuracy_season'),
        ('danger_zone_ratio', 'danger_zone_ratio_season'),
        ('shots_on_target_per_match', 'shots_on_target_per_match_season'),
        ('finishing_efficiency', 'finishing_efficiency_season'),
        ('duels_per_match', 'duels_per_match_season'),
        ('duels_won_pct', 'duels_won_pct_season'),
        ('defensive_actions_per_match', 'defensive_actions_per_match_season'),
        ('tackles_per_match', 'tackles_per_match_season'),
        ('interceptions_per_match', 'interceptions_per_match_season'),
        ('blocks_per_match', 'blocks_per_match_season'),
        ('passes_per_match', 'passes_per_match_season'),
        ('pass_accuracy', 'pass_accuracy_season'),
        ('key_passes_per_match', 'key_passes_per_match_season'),
        ('corner_kicks_per_match', 'corner_kicks_per_match_season'),
        ('corners_conceded_per_match', 'corners_conceded_per_match_season'),
        ('save_ratio', 'save_ratio_season')
    ] %}
    {{ return(metrics) }}
{% endmacro %}
