{#
  The player metrics the page compares, and the positions each is compared for: a metric for
  goalkeepers on saves, goals against and passing, for outfield players on every metric but those of
  the goal. A list of structs to unnest over a row of the metric columns named by `alias`.
  with_floors applies the shots-on-target floor of the ranking_rules doc block, which only the
  competition benchmark has.
#}
{% macro player_benchmark_metrics(alias, with_floors=true) %}
    [
        struct(
            'saves_per90' as metric_key,
            ['GK'] as position_groups,
            true as is_qualified,
            {{ alias }}.saves_per90 as metric_value,
            cast(null as int64) as metric_numerator,
            cast(null as int64) as metric_denominator
        ),
        (
            'saves_player_pct', ['GK'], true, {{ alias }}.saves_player_pct,
            {{ alias }}.saves_player, {{ alias }}.saves_player + {{ alias }}.goals_against_player
        ),
        ('goals_against_per90', ['GK'], true, {{ alias }}.goals_against_per90, null, null),
        ('passes_per90', ['GK', 'DEF', 'MID', 'ATT'], true, {{ alias }}.passes_per90, null, null),
        ('ball_actions_per90', ['GK', 'DEF', 'MID', 'ATT'], true, {{ alias }}.ball_actions_per90, null, null),
        (
            'passes_accuracy_player_pct', ['GK', 'DEF', 'MID', 'ATT'], true, {{ alias }}.passes_accuracy_player_pct,
            {{ alias }}.passes_accurate_player, {{ alias }}.passes_player
        ),
        ('goals_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.goals_per90, null, null),
        ('assists_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.assists_per90, null, null),
        ('scorer_points_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.scorer_points_per90, null, null),
        ('shots_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.shots_per90, null, null),
        ('shots_on_goal_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.shots_on_goal_per90, null, null),
        (
            'shots_on_goal_player_pct', ['DEF', 'MID', 'ATT'], true, {{ alias }}.shots_on_goal_player_pct,
            {{ alias }}.shots_on_goal_player, {{ alias }}.shots_player
        ),
        ('passes_key_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.passes_key_per90, null, null),
        (
            'finishing_efficiency_player_pct', ['DEF', 'MID', 'ATT'],
            {% if with_floors %}
                {{ alias }}.shots_on_goal_player >= {{ var('player_min_shots_on_target') }},
            {% else %}
                true,
            {% endif %}
            {{ alias }}.finishing_efficiency_player_pct,
            {{ alias }}.goals_player - {{ alias }}.goals_penalty_player, {{ alias }}.shots_on_goal_player
        ),
        ('dribbles_success_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.dribbles_success_per90, null, null),
        (
            'dribbles_success_player_pct', ['DEF', 'MID', 'ATT'], true, {{ alias }}.dribbles_success_player_pct,
            {{ alias }}.dribbles_success_player, {{ alias }}.dribbles_attempts_player
        ),
        ('duels_won_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.duels_won_per90, null, null),
        (
            'duels_won_player_pct', ['DEF', 'MID', 'ATT'], true, {{ alias }}.duels_won_player_pct,
            {{ alias }}.duels_won_player, {{ alias }}.duels_player
        ),
        ('defensive_actions_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.defensive_actions_per90, null, null),
        ('tackles_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.tackles_per90, null, null),
        ('interceptions_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.interceptions_per90, null, null),
        ('blocks_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.blocks_per90, null, null),
        ('fouls_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.fouls_per90, null, null),
        ('offsides_per90', ['DEF', 'MID', 'ATT'], true, {{ alias }}.offsides_per90, null, null)
    ]
{% endmacro %}
