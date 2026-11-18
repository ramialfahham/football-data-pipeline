{#
  The team competition-benchmark metrics in LONG form, per team-season: one row per
  (team_sk, season_sk, metric_key) unpivoted from int_team_season__metrics (season-to-date, teams with
  at least the var team_min_matches finished games). The set is every team metric the site's served
  list shows (metric_rows.json) plus the shots-on-target difference and the clean-sheet share. This is the single source of the
  benchmark metric set — both int_team_competition_benchmarks (which aggregates it to the league
  distribution) and mart_team_competition_benchmarks (which ranks each team against that
  distribution) read from here, so the two cannot drift apart. BigQuery UNPIVOT excludes nulls, so a
  metric with no value for a team (e.g. a player-stat coverage gap) simply yields no row. Counts are
  cast to FLOAT64, the one type an UNPIVOT column list holds.

  An international club competition with a league or group phase is benchmarked over that phase
  alone (int_team_competition_phase__metrics): its teams and its matches, without the qualifiers
  and the knockout phase. Every other competition-season counts all its matches. round_stage_kind
  says which: table for a competition-season benchmarked over its table rounds, NULL otherwise.
  Grain: (team_sk, season_sk, metric_key).
#}

with phase as (
    select * from {{ ref('int_team_competition_phase__metrics') }}
),

all_matches as (
    select m.*
    from {{ ref('int_team_season__metrics') }} as m
    where m.season_sk not in (select p.season_sk from phase as p)
),

season as (
    {% for source in ['all_matches', 'phase'] %}
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        {{ "'table'" if source == 'phase' else 'cast(null as string)' }} as round_stage_kind,
        season_games_played,
        goals_per_match,
        goals_against_per_match,
        cast(clean_sheets as float64) as clean_sheets,
        clean_sheets_pct,
        shots_per_match,
        shots_on_goal_pct,
        shots_inside_box_pct,
        shots_inside_box_per_match,
        shots_on_goal_per_match,
        shots_on_goal_against_per_match,
        shots_on_goal_difference_per_match,
        finishing_efficiency_pct,
        duels_per_match,
        duels_won_per_match,
        duels_won_pct,
        defensive_actions_per_match,
        tackles_per_match,
        interceptions_per_match,
        blocks_per_match,
        passes_per_match,
        passes_accurate_per_match,
        passes_accuracy_pct,
        passes_share_pct,
        passes_key_per_match,
        dribbles_attempts_per_match,
        dribbles_success_per_match,
        dribbles_success_pct,
        corners_per_match,
        corners_against_per_match,
        free_kicks_per_match,
        fouls_per_match,
        offsides_per_match,
        saves_per_match,
        saves_pct,
        cast(cards_yellow as float64) as cards_yellow,
        cast(cards_red as float64) as cards_red
    from {{ source }}
    where season_games_played >= {{ var('team_min_matches') }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
),

current_long as (
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        round_stage_kind,
        metric_key,
        metric_value
    from season
    unpivot (
        metric_value for metric_key in (
            goals_per_match,
            goals_against_per_match,
            clean_sheets,
            clean_sheets_pct,
            shots_per_match,
            shots_on_goal_pct,
            shots_inside_box_pct,
            shots_inside_box_per_match,
            shots_on_goal_per_match,
            shots_on_goal_against_per_match,
            shots_on_goal_difference_per_match,
            finishing_efficiency_pct,
            duels_per_match,
            duels_won_per_match,
            duels_won_pct,
            defensive_actions_per_match,
            tackles_per_match,
            interceptions_per_match,
            blocks_per_match,
            passes_per_match,
            passes_accurate_per_match,
            passes_accuracy_pct,
            passes_share_pct,
            passes_key_per_match,
            dribbles_attempts_per_match,
            dribbles_success_per_match,
            dribbles_success_pct,
            corners_per_match,
            corners_against_per_match,
            free_kicks_per_match,
            fouls_per_match,
            offsides_per_match,
            saves_per_match,
            saves_pct,
            cards_yellow,
            cards_red
        )
    )
)

select
    cur.team_sk,
    cur.season_sk,
    cur.league_sk,
    cur.league_code,
    cur.season_api_year,
    cur.round_stage_kind,
    cur.metric_key,
    cur.metric_value
from current_long as cur
