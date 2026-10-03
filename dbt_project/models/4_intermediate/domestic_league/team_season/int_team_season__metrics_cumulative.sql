{#
  Per-matchday cumulative team-season metrics — the catalogue formulas applied to the season
  window of int_team_season_record at EVERY matchday (the totals THROUGH each match), not just the
  final one. This is the single home of the team-season metrics:

    - int_team_season__metrics is the FINAL-ROW PROJECTION of this model (whole-season rollup).
    - int_team_profile__yoy COMPOSES this model at the games-played cutoff N to align two seasons
      by matchday for ALL metrics ("this season through N vs last season through its first N").

  Grain: (team_sk, league_code, season_api_year, match_number). All-competitions, like
  int_team_season__metrics (no domestic filter — the YoY consumer applies that).

  Every catalogue metric is written by scripts/generate_metric_sql.py from metric_catalogue.csv,
  by the rules in models/docs/metric_rules.md. The match counts, the coverage counts and the raw
  tallies of inputs no catalogue metric names (the *_sum_season columns) are hand-written here and
  follow the same rules. NAMING NOTE: the `_sum_season` /
  `season_games_played` / `stat_coverage_season_games` names are kept for the whole-season
  projection; here they mean "cumulative THROUGH THIS matchday".
#}

with rec as (
    select * from {{ ref('int_team_season_record') }}
)

select
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    entity_type,
    match_number,
    count(*) over w as season_games_played,
    countif(shots_on_target is not null) over w as stat_coverage_season_games,
    countif(has_player_stats) over w as player_stat_coverage_season_games,
    countif(shots is not null) over w as games_with_team_stats,
    countif(not is_awarded_result) over w as games_expecting_team_stats,
    countif(result = 'W') over w as wins_sum_season,
    countif(result = 'D') over w as draws_sum_season,
    countif(result = 'L') over w as losses_sum_season,
    if(
        logical_and(is_awarded_result or shots is not null) over w,
        sum(if(is_awarded_result, null, shots)) over w,
        null
    ) as total_shots_sum_season,
    if(
        logical_and(is_awarded_result or shots_against is not null) over w,
        sum(if(is_awarded_result, null, shots_against)) over w,
        null
    ) as opponent_total_shots_sum_season,
    if(
        logical_and(is_awarded_result or shots_on_target is not null) over w,
        sum(if(is_awarded_result, null, shots_on_target)) over w,
        null
    ) as shots_on_goal_sum_season,
    if(
        logical_and(is_awarded_result or corners_against is not null) over w,
        sum(if(is_awarded_result, null, corners_against)) over w,
        null
    ) as opponent_corner_kicks_sum_season,
    if(
        logical_and(is_awarded_result or passes_accurate is not null) over w,
        sum(if(is_awarded_result, null, passes_accurate)) over w,
        null
    ) as passes_accurate_sum_season,
    if(
        logical_and(is_awarded_result or passes is not null) over w,
        sum(if(is_awarded_result, null, passes)) over w,
        null
    ) as passes_total_sum_season,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
    if(
        logical_and((case result when 'W' then 3 when 'D' then 1 else 0 end) is not null) over w,
        sum(case result when 'W' then 3 when 'D' then 1 else 0 end) over w,
        null
    ) as points_won,
    if(logical_and(goals is not null) over w, sum(goals) over w, null) as goals,
    if(logical_and(goals_against is not null) over w, sum(goals_against) over w, null) as goals_against,
    if(
        logical_and(is_awarded_result or (goals_against = 0) is not null) over w,
        countif(not is_awarded_result and (goals_against = 0)) over w,
        null
    ) as clean_sheets,
    if(
        logical_and(is_awarded_result or goals_penalty is not null) over w,
        sum(if(is_awarded_result, null, goals_penalty)) over w,
        null
    ) as goals_penalty,
    if(
        logical_and(is_awarded_result or goals_own is not null) over w,
        sum(if(is_awarded_result, null, goals_own)) over w,
        null
    ) as goals_own,
    if(
        logical_and(is_awarded_result or (goals - goals_penalty - goals_own) is not null) over w,
        sum(if(is_awarded_result, null, goals - goals_penalty - goals_own)) over w,
        null
    ) as goals_open_play,
    if(
        logical_and(is_awarded_result or corners is not null) over w,
        sum(if(is_awarded_result, null, corners)) over w,
        null
    ) as corners,
    if(
        logical_and(is_awarded_result or saves is not null) over w,
        sum(if(is_awarded_result, null, saves)) over w,
        null
    ) as saves,
    if(
        logical_and(is_awarded_result or shots_inside_box is not null) over w,
        sum(if(is_awarded_result, null, shots_inside_box)) over w,
        null
    ) as shots_inside_box,
    if(
        logical_and(is_awarded_result or cards_yellow is not null) over w,
        sum(if(is_awarded_result, null, cards_yellow)) over w,
        null
    ) as cards_yellow,
    if(
        logical_and(is_awarded_result or cards_red is not null) over w,
        sum(if(is_awarded_result, null, cards_red)) over w,
        null
    ) as cards_red,
    safe_divide(
        if(
            logical_and(is_awarded_result or goals is not null) over w,
            sum(if(is_awarded_result, null, goals)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as goals_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or goals_against is not null) over w,
            sum(if(is_awarded_result, null, goals_against)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as goals_against_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots is not null) over w,
            sum(if(is_awarded_result, null, shots)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as shots_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_on_target is not null) over w,
            sum(if(is_awarded_result, null, shots_on_target)) over w,
            null
        ),
        if(
            logical_and(is_awarded_result or shots is not null) over w,
            sum(if(is_awarded_result, null, shots)) over w,
            null
        )
    ) as shots_on_goal_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_inside_box is not null) over w,
            sum(if(is_awarded_result, null, shots_inside_box)) over w,
            null
        ),
        if(
            logical_and(is_awarded_result or shots is not null) over w,
            sum(if(is_awarded_result, null, shots)) over w,
            null
        )
    ) as shots_inside_box_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_on_target is not null) over w,
            sum(if(is_awarded_result, null, shots_on_target)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as shots_on_goal_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or (goals - goals_penalty - goals_own) is not null) over w,
            sum(if(is_awarded_result, null, goals - goals_penalty - goals_own)) over w,
            null
        ),
        if(
            logical_and(is_awarded_result or shots_on_target is not null) over w,
            sum(if(is_awarded_result, null, shots_on_target)) over w,
            null
        )
    ) as finishing_efficiency_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or passes is not null) over w,
            sum(if(is_awarded_result, null, passes)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as passes_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or passes_accurate is not null) over w,
            sum(if(is_awarded_result, null, passes_accurate)) over w,
            null
        ),
        if(
            logical_and(is_awarded_result or passes is not null) over w,
            sum(if(is_awarded_result, null, passes)) over w,
            null
        )
    ) as passes_accuracy_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or corners is not null) over w,
            sum(if(is_awarded_result, null, corners)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as corners_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or corners_against is not null) over w,
            sum(if(is_awarded_result, null, corners_against)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as corners_against_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or saves is not null) over w,
            sum(if(is_awarded_result, null, saves)) over w,
            null
        ),
        if(
            logical_and(is_awarded_result or (saves + goals_against - goals_own_against) is not null) over w,
            sum(if(is_awarded_result, null, saves + goals_against - goals_own_against)) over w,
            null
        )
    ) as saves_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or passes_key is not null) over w,
            sum(if(is_awarded_result, null, passes_key)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as passes_key_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or tackles is not null) over w,
            sum(if(is_awarded_result, null, tackles)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as tackles_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or interceptions is not null) over w,
            sum(if(is_awarded_result, null, interceptions)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as interceptions_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or blocks is not null) over w,
            sum(if(is_awarded_result, null, blocks)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as blocks_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or (tackles + interceptions + blocks) is not null) over w,
            sum(if(is_awarded_result, null, tackles + interceptions + blocks)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as defensive_actions_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or duels is not null) over w,
            sum(if(is_awarded_result, null, duels)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as duels_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or duels_won is not null) over w,
            sum(if(is_awarded_result, null, duels_won)) over w,
            null
        ),
        if(
            logical_and(is_awarded_result or duels is not null) over w,
            sum(if(is_awarded_result, null, duels)) over w,
            null
        )
    ) as duels_won_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or (goals_against = 0) is not null) over w,
            countif(not is_awarded_result and (goals_against = 0)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as clean_sheets_pct,
    safe_divide(
        if(
            logical_and(
                is_awarded_result or (case result when 'W' then 3 when 'D' then 1 else 0 end) is not null
            ) over w,
            sum(if(is_awarded_result, null, case result when 'W' then 3 when 'D' then 1 else 0 end)) over w,
            null
        ),
        3 * countif(not is_awarded_result) over w
    ) as points_capture_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots is not null) over w,
            sum(if(is_awarded_result, null, shots)) over w,
            null
        ),
        if(
            logical_and(is_awarded_result or (shots + shots_against) is not null) over w,
            sum(if(is_awarded_result, null, shots + shots_against)) over w,
            null
        )
    ) as shots_share_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_on_target_against is not null) over w,
            sum(if(is_awarded_result, null, shots_on_target_against)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as shots_on_goal_against_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or (shots_on_target - shots_on_target_against) is not null) over w,
            sum(if(is_awarded_result, null, shots_on_target - shots_on_target_against)) over w,
            null
        ),
        countif(not is_awarded_result) over w
    ) as shots_on_goal_difference_per_match
    -- end of generated metric sql
from rec
window
    w as (
        partition by team_sk, league_code, season_api_year
        order by kickoff_datetime asc, fixture_sk asc
        rows between unbounded preceding and current row
    )
