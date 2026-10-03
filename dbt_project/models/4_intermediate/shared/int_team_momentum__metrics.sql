{#
  W1 momentum builder — team.

  Applies the catalogue formulas to the window legs selected by int_team_momentum_window
  (the selection was extracted there in #323 so this aggregate and the drill-down list
  mart consume the same matches). The window is last-5 for most competitions and
  cumulative (tournament_to_date / qualifiers) for tournament fixtures (GAP-18); the
  window_type carried from the selection says which, and games_in_window is the actual
  count (1–5 for last_5, unbounded for tournament windows).

  Grain: (upcoming_fixture_sk, team_sk).

  Scope: all competition types — club and national. W1 is shown alongside W2 for every
  fixture; both numbers are always presented together.

  Returns no row when a team has no finished matches yet (before phase for a
  club domestic_league). The mart will emit nulls; #326 fills the gap.

  Every catalogue metric is written by scripts/generate_metric_sql.py from metric_catalogue.csv
  over the window's legs, with the team totals from players joined to them, by the rules in
  docs/metric_layer.md. The match and coverage counts are hand-written.
#}

with window_legs as (
    select * from {{ ref('int_team_momentum_window') }}
),

window_rows as (
    select
        wl.*,
        p.passes_key,
        p.tackles,
        p.interceptions,
        p.blocks,
        p.duels,
        p.duels_won,
        p.fixture_sk is not null as has_player_stats
    from window_legs as wl
    left join {{ ref('int_legs__team_from_players') }} as p
        on
            wl.leg_fixture_sk = p.fixture_sk
            and wl.team_sk = p.team_sk
)

select
    upcoming_fixture_sk,
    team_sk,
    season_api_year,
    entity_type,
    window_type,
    count(*) as games_in_window,
    -- the window's games that can carry a stat line: an awarded result (AWD / WO) is decided off
    -- the pitch and has none
    countif(not is_awarded_result) as games_expecting_team_stats,
    countif(shots is not null) as games_with_team_stats,
    countif(has_player_stats) as games_with_player_stats,
    array_agg(distinct leg_league_code order by leg_league_code) as contributing_competitions,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
    if(
        logical_and((case result when 'W' then 3 when 'D' then 1 else 0 end) is not null),
        sum(case result when 'W' then 3 when 'D' then 1 else 0 end),
        null
    ) as points_won,
    if(
        logical_and(is_awarded_result or (goals_against = 0) is not null),
        countif(not is_awarded_result and (goals_against = 0)),
        null
    ) as clean_sheets,
    safe_divide(
        if(logical_and(is_awarded_result or goals is not null), sum(if(is_awarded_result, null, goals)), null),
        countif(not is_awarded_result)
    ) as goals_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or goals_against is not null),
            sum(if(is_awarded_result, null, goals_against)),
            null
        ),
        countif(not is_awarded_result)
    ) as goals_against_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or shots is not null), sum(if(is_awarded_result, null, shots)), null),
        countif(not is_awarded_result)
    ) as shots_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_on_target is not null),
            sum(if(is_awarded_result, null, shots_on_target)),
            null
        ),
        if(
            logical_and(is_awarded_result or shots is not null),
            sum(if(is_awarded_result, null, shots)),
            null
        )
    ) as shots_on_goal_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_inside_box is not null),
            sum(if(is_awarded_result, null, shots_inside_box)),
            null
        ),
        if(
            logical_and(is_awarded_result or shots is not null),
            sum(if(is_awarded_result, null, shots)),
            null
        )
    ) as shots_inside_box_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_on_target is not null),
            sum(if(is_awarded_result, null, shots_on_target)),
            null
        ),
        countif(not is_awarded_result)
    ) as shots_on_goal_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or (goals - goals_penalty - goals_own) is not null),
            sum(if(is_awarded_result, null, goals - goals_penalty - goals_own)),
            null
        ),
        if(
            logical_and(is_awarded_result or shots_on_target is not null),
            sum(if(is_awarded_result, null, shots_on_target)),
            null
        )
    ) as finishing_efficiency_pct,
    safe_divide(
        if(logical_and(is_awarded_result or passes is not null), sum(if(is_awarded_result, null, passes)), null),
        countif(not is_awarded_result)
    ) as passes_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or passes_accurate is not null),
            sum(if(is_awarded_result, null, passes_accurate)),
            null
        ),
        if(
            logical_and(is_awarded_result or passes is not null),
            sum(if(is_awarded_result, null, passes)),
            null
        )
    ) as passes_accuracy_pct,
    safe_divide(
        if(logical_and(is_awarded_result or corners is not null), sum(if(is_awarded_result, null, corners)), null),
        countif(not is_awarded_result)
    ) as corners_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or corners_against is not null),
            sum(if(is_awarded_result, null, corners_against)),
            null
        ),
        countif(not is_awarded_result)
    ) as corners_against_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or saves is not null),
            sum(if(is_awarded_result, null, saves)),
            null
        ),
        if(
            logical_and(is_awarded_result or (saves + goals_against - goals_own_against) is not null),
            sum(if(is_awarded_result, null, saves + goals_against - goals_own_against)),
            null
        )
    ) as saves_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or passes_key is not null),
            sum(if(is_awarded_result, null, passes_key)),
            null
        ),
        countif(not is_awarded_result)
    ) as passes_key_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or tackles is not null), sum(if(is_awarded_result, null, tackles)), null),
        countif(not is_awarded_result)
    ) as tackles_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or interceptions is not null),
            sum(if(is_awarded_result, null, interceptions)),
            null
        ),
        countif(not is_awarded_result)
    ) as interceptions_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or blocks is not null), sum(if(is_awarded_result, null, blocks)), null),
        countif(not is_awarded_result)
    ) as blocks_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or (tackles + interceptions + blocks) is not null),
            sum(if(is_awarded_result, null, tackles + interceptions + blocks)),
            null
        ),
        countif(not is_awarded_result)
    ) as defensive_actions_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or duels is not null), sum(if(is_awarded_result, null, duels)), null),
        countif(not is_awarded_result)
    ) as duels_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or duels_won is not null), sum(if(is_awarded_result, null, duels_won)), null),
        if(logical_and(is_awarded_result or duels is not null), sum(if(is_awarded_result, null, duels)), null)
    ) as duels_won_pct
    -- end of generated metric sql
from window_rows
group by
    upcoming_fixture_sk,
    team_sk,
    season_api_year,
    entity_type,
    window_type
