{{ config(materialized='view') }}

{#
  The 22 team competition-benchmark metrics in LONG form, per team-season: one row per
  (team_sk, season_sk, metric_key) unpivoted from int_team_season__metrics (season-to-date, teams with
  >= 3 finished games). This is the single source of the benchmark metric set — both
  int_team_competition_benchmarks (which aggregates it to the league distribution) and
  mart_team_competition_benchmarks (which ranks each team against that distribution) read from here, so
  the two cannot drift apart. Replaces the team_benchmark_metrics() macro (engineering_standards.md §1.3:
  a shared list belongs in a model, not a macro). BigQuery UNPIVOT excludes nulls, so a metric with no
  value for a team (e.g. a player-stat coverage gap) simply yields no row — the same teams the prior
  `where metric_value is not null` filters dropped.
  Grain: (team_sk, season_sk, metric_key).
#}

with season as (
    select * from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 3
)

select
    team_sk,
    season_sk,
    league_sk,
    league_code,
    season_api_year,
    metric_key,
    metric_value
from season
unpivot (
    metric_value for metric_key in (
        goals_per_match,
        goals_against_per_match,
        clean_sheets_pct,
        shots_per_match,
        shots_on_goal_pct,
        shots_inside_box_pct,
        shots_on_goal_per_match,
        shots_on_goal_against_per_match,
        sot_difference_per_match,
        finishing_efficiency,
        duels_per_match,
        duels_won_pct,
        defensive_actions_per_match,
        tackles_per_match,
        interceptions_per_match,
        blocks_per_match,
        passes_per_match,
        pass_accuracy,
        key_passes_per_match,
        corners_per_match,
        corners_against_per_match,
        saves_pct
    )
)
