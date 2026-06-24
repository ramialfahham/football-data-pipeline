{% macro player_benchmark_metrics() %}
{#
  The 18 player season metrics the competition benchmark covers, with per-metric POSITION ELIGIBILITY.
  Single source so the benchmark intermediate (the per-position distribution) and the mart (per-player
  value + rank + percentile) cannot drift apart — the player analog of team_benchmark_metrics().

  Each entry: key = the metric_catalogue metric_id; col = the column in int_player_season_position__metrics;
  pos = the position groups this metric is benchmarked for (eligibility — CPO ruling 2026-06-23 B3); floor
  (optional) = an extra per-row qualifier on top of the global minutes >= 270 (finishing needs >= 10 shots
  on target in the position).

  Eligibility rule (CPO B3): benchmark a metric for a position only when non-degenerate for that group.
  Because the peer pool is already position-specific, the only dead boards are at the GK<->outfield
  boundary, so eligibility is essentially binary: GK = the 4 keeper metrics (shot-stopping + distribution);
  DEF = MID = ATT = the other 16. No finer outfield split — a CB's goals_per90 is ranked only vs other CBs.
#}
    {% set outfield = ['DEF', 'MID', 'ATT'] %}
    {% set all_pos = ['GK', 'DEF', 'MID', 'ATT'] %}
    {% set metrics = [
        {'key': 'saves_per90', 'col': 'saves_per90', 'pos': ['GK']},
        {'key': 'save_pct', 'col': 'save_pct', 'pos': ['GK']},
        {'key': 'passes_per90', 'col': 'passes_per90', 'pos': all_pos},
        {'key': 'pass_accuracy_pct', 'col': 'pass_accuracy_pct', 'pos': all_pos},
        {'key': 'goals_per90', 'col': 'goals_per90', 'pos': outfield},
        {'key': 'assists_per90', 'col': 'assists_per90', 'pos': outfield},
        {'key': 'scorer_points_per90', 'col': 'scorer_points_per90', 'pos': outfield},
        {'key': 'shots_on_goal_per90', 'col': 'shots_on_goal_per90', 'pos': outfield},
        {'key': 'key_passes_per90', 'col': 'key_passes_per90', 'pos': outfield},
        {'key': 'finishing_efficiency', 'col': 'finishing_efficiency', 'pos': outfield, 'floor': 'shots_on_goal >= 10'},
        {'key': 'dribbles_success_per90', 'col': 'dribbles_success_per90', 'pos': outfield},
        {'key': 'dribbles_success_pct', 'col': 'dribbles_success_pct', 'pos': outfield},
        {'key': 'duels_won_per90', 'col': 'duels_won_per90', 'pos': outfield},
        {'key': 'duels_won_pct', 'col': 'duels_won_pct', 'pos': outfield},
        {'key': 'defensive_actions_per90', 'col': 'defensive_actions_per90', 'pos': outfield},
        {'key': 'tackles_per90', 'col': 'tackles_per90', 'pos': outfield},
        {'key': 'interceptions_per90', 'col': 'interceptions_per90', 'pos': outfield},
        {'key': 'blocks_per90', 'col': 'blocks_per90', 'pos': outfield}
    ] %}
    {{ return(metrics) }}
{% endmacro %}
