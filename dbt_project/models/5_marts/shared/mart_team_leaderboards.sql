{{ config(materialized='view') }}

{#
  mart_team_leaderboards — LONG per-board team rankings (the Top teams block; GAP-29). The team
  mirror of mart_leaderboards. One row per (team, board): where that team ranks on that board
  within its competition-season. Season-to-date, composed from int_team_season__metrics (the
  canonical whole-season team rollup) + dim_team identity — NOT mart-from-mart.

  FOUR boards (CPO 2026-08-10), single-metric like the reduced player boards: goals_per_match,
  shots_on_goal_per_match, passes_per_match, duels_per_match. All four are higher_better in the
  metric catalogue, so one shared DESC order is correct for every board — a lower-is-better board
  would need its own direction and there is none here.

  rank = DENSE_RANK over the board's metric desc within (league_code, season_api_year): ties share a
  rank, no ranks are skipped, and the top-10 cut is inclusive of ties (the mart_leaderboards
  convention). The partition is per league by CPO ruling 2026-08-18 — "one team per league, same as
  players" — so a board is each league's rank-1 team collected and ordered, and the ranking never
  crosses league_code. That also satisfies the block's rule that club and national-team
  competitions are never mixed: every competition is already its own ranking.

  Qualification is the >= 3 finished games gate that int_team_competition_benchmark_metrics_long
  already applies. The player mart's minutes/position floors have no analogue here: team metrics are
  per-match rates already, so the games gate IS the small-sample guard.

  UNPIVOT rather than mart_leaderboards' union-all loop, because all four boards share one rule —
  the union there exists to give each rate board its own qualification WHERE. BigQuery UNPIVOT
  excludes nulls, so a metric with no value for a team (a coverage gap) yields no row rather than a
  null rank. Source is int_team_season__metrics, deliberately NOT the benchmark long form: that
  model is the single source of the BENCHMARK metric set, and reading it here would couple this
  block's boards to that set.

  Grain: (team_sk, season_sk, metric_key).
#}

{# The board set. Adding or removing a key here must also move seeds' accepted_values AND the
   singular test — accepted_values alone is blind to a REMOVED board (a smaller set is still a
   subset), which is the silent direction. #}
{% set boards = [
    'goals_per_match',
    'shots_on_goal_per_match',
    'passes_per_match',
    'duels_per_match',
] %}

with season as (
    select * from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 3
),

-- One row per (team-season, board). UNPIVOT drops nulls, so a team missing a metric through a
-- coverage gap is absent from that board rather than ranked on a null.
long as (
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        season_games_played,
        metric_key,
        metric_value
    from season
    unpivot (
        metric_value for metric_key in (
            {% for board in boards %}
            {{ board }}{% if not loop.last %},{% endif %}
            {% endfor %}
        )
    )
),

-- Identity only. dim_team is unique on team_sk, so the left join cannot fan the row count out.
teams as (
    select
        team_sk,
        team_name,
        team_slug,
        team_logo_url
    from {{ ref('dim_team') }}
),

base as (
    select
        l.team_sk,
        l.season_sk,
        l.league_sk,
        l.league_code,
        l.season_api_year,
        l.season_games_played,
        l.metric_key,
        l.metric_value,
        t.team_name,
        t.team_slug,
        t.team_logo_url
    from long as l
    left join teams as t on l.team_sk = t.team_sk
),

ranked as (
    select
        base.*,
        dense_rank() over (
            partition by league_code, season_api_year, metric_key
            order by metric_value desc
        ) as board_rank
    from base
    where metric_value > 0
)

select
    {{ dbt_utils.generate_surrogate_key(['team_sk', 'season_sk', 'metric_key']) }}
        as team_leaderboard_sk,
    metric_key,
    board_rank as rank,
    metric_value as sort_value,
    league_code,
    season_api_year,
    season_sk,
    league_sk,
    team_sk,
    team_name,
    team_slug,
    team_logo_url,
    season_games_played
from ranked
where board_rank <= 10
