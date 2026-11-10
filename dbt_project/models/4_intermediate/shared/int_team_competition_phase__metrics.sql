{#
  An international club competition's season over its league or group phase only: every team with
  a match in a round whose round_stage_kind is table (int_round_names), and its metrics over those
  matches. Qualifying rounds, play-offs and the knockout phase are left out, so the competition's
  benchmarks rank a club among the phase's teams. An international club competition is a club
  competition other than a domestic league or domestic cup; one with no table round has no row.

  Every metric is its catalogue formula over the phase's matches, written by
  scripts/generate_metric_sql.py by the rules in models/docs/metric_rules.md.

  Grain: (team_sk, season_sk).
#}

with competitions as (
    select league_code
    from {{ ref('dim_league') }}
    where
        entity_type = 'club'
        and competition_type not in ('domestic_league', 'domestic_cup')
),

table_rounds as (
    select
        league_code,
        season_api_year,
        round_name
    from {{ ref('int_round_names') }}
    where round_stage_kind = 'table'
),

phase_rows as (
    select
        legs.*,
        p.passes_key,
        p.tackles,
        p.interceptions,
        p.blocks,
        p.duels,
        p.duels_won,
        p.dribbles,
        p.dribbles_success
    from {{ ref('int_legs__team_match') }} as legs
    inner join competitions as c
        on legs.league_code = c.league_code
    inner join table_rounds as r
        on
            legs.league_code = r.league_code
            and legs.season_api_year = r.season_api_year
            and legs.round_name = r.round_name
    left join {{ ref('int_legs__team_from_players') }} as p
        on
            legs.fixture_sk = p.fixture_sk
            and legs.team_sk = p.team_sk
)

select
    team_sk,
    season_sk,
    league_sk,
    league_code,
    season_api_year,
    count(*) as season_games_played,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
    if(
        logical_and((case result when 'W' then 3 when 'D' then 1 else 0 end) is not null),
        sum(case result when 'W' then 3 when 'D' then 1 else 0 end),
        null
    ) + if(
        logical_and(is_table_shootout_win is not null),
        countif(is_table_shootout_win),
        null
    ) as points_won,
    if(logical_and(goals is not null), sum(goals), null) as goals,
    if(logical_and(goals_against is not null), sum(goals_against), null) as goals_against,
    if(
        logical_and(is_awarded_result or (goals_against = 0) is not null),
        countif(not is_awarded_result and (goals_against = 0)),
        null
    ) as clean_sheets,
    if(
        logical_and(is_awarded_result or goals_penalty is not null),
        sum(if(is_awarded_result, null, goals_penalty)),
        null
    ) as goals_penalty,
    if(
        logical_and(is_awarded_result or goals_own is not null),
        sum(if(is_awarded_result, null, goals_own)),
        null
    ) as goals_own,
    if(
        logical_and(is_awarded_result or (goals - goals_penalty - goals_own) is not null),
        sum(if(is_awarded_result, null, goals - goals_penalty - goals_own)),
        null
    ) as goals_open_play,
    if(
        logical_and(is_awarded_result or corners is not null),
        sum(if(is_awarded_result, null, corners)),
        null
    ) as corners,
    if(logical_and(is_awarded_result or saves is not null), sum(if(is_awarded_result, null, saves)), null) as saves,
    if(
        logical_and(is_awarded_result or shots_inside_box is not null),
        sum(if(is_awarded_result, null, shots_inside_box)),
        null
    ) as shots_inside_box,
    if(
        logical_and(is_awarded_result or cards_yellow is not null),
        sum(if(is_awarded_result, null, cards_yellow)),
        null
    ) as cards_yellow,
    if(
        logical_and(is_awarded_result or cards_red is not null),
        sum(if(is_awarded_result, null, cards_red)),
        null
    ) as cards_red,
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
    ) as duels_won_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_on_target_against is not null),
            sum(if(is_awarded_result, null, shots_on_target_against)),
            null
        ),
        countif(not is_awarded_result)
    ) as shots_on_goal_against_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_off_target is not null),
            sum(if(is_awarded_result, null, shots_off_target)),
            null
        ),
        countif(not is_awarded_result)
    ) as shots_off_target_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_blocked is not null),
            sum(if(is_awarded_result, null, shots_blocked)),
            null
        ),
        countif(not is_awarded_result)
    ) as shots_blocked_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots_inside_box is not null),
            sum(if(is_awarded_result, null, shots_inside_box)),
            null
        ),
        countif(not is_awarded_result)
    ) as shots_inside_box_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or passes_accurate is not null),
            sum(if(is_awarded_result, null, passes_accurate)),
            null
        ),
        countif(not is_awarded_result)
    ) as passes_accurate_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or passes is not null),
            sum(if(is_awarded_result, null, passes)),
            null
        ),
        if(
            logical_and(is_awarded_result or (passes + passes_against) is not null),
            sum(if(is_awarded_result, null, passes + passes_against)),
            null
        )
    ) as passes_share_pct,
    safe_divide(
        if(logical_and(is_awarded_result or dribbles is not null), sum(if(is_awarded_result, null, dribbles)), null),
        countif(not is_awarded_result)
    ) as dribbles_attempts_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or dribbles_success is not null),
            sum(if(is_awarded_result, null, dribbles_success)),
            null
        ),
        countif(not is_awarded_result)
    ) as dribbles_success_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or dribbles_success is not null),
            sum(if(is_awarded_result, null, dribbles_success)),
            null
        ),
        if(
            logical_and(is_awarded_result or dribbles is not null),
            sum(if(is_awarded_result, null, dribbles)),
            null
        )
    ) as dribbles_success_pct,
    safe_divide(
        if(logical_and(is_awarded_result or duels_won is not null), sum(if(is_awarded_result, null, duels_won)), null),
        countif(not is_awarded_result)
    ) as duels_won_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or saves is not null), sum(if(is_awarded_result, null, saves)), null),
        countif(not is_awarded_result)
    ) as saves_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or free_kicks is not null),
            sum(if(is_awarded_result, null, free_kicks)),
            null
        ),
        countif(not is_awarded_result)
    ) as free_kicks_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or fouls is not null), sum(if(is_awarded_result, null, fouls)), null),
        countif(not is_awarded_result)
    ) as fouls_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or offsides is not null), sum(if(is_awarded_result, null, offsides)), null),
        countif(not is_awarded_result)
    ) as offsides_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or cards_yellow is not null),
            sum(if(is_awarded_result, null, cards_yellow)),
            null
        ),
        countif(not is_awarded_result)
    ) as cards_yellow_per_match,
    safe_divide(
        if(logical_and(is_awarded_result or cards_red is not null), sum(if(is_awarded_result, null, cards_red)), null),
        countif(not is_awarded_result)
    ) as cards_red_per_match,
    safe_divide(
        if(
            logical_and(is_awarded_result or (goals_against = 0) is not null),
            countif(not is_awarded_result and (goals_against = 0)),
            null
        ),
        countif(not is_awarded_result)
    ) as clean_sheets_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or (case result when 'W' then 3 when 'D' then 1 else 0 end) is not null),
            sum(if(is_awarded_result, null, case result when 'W' then 3 when 'D' then 1 else 0 end)),
            null
        ) + if(
            logical_and(is_awarded_result or is_table_shootout_win is not null),
            countif(not is_awarded_result and is_table_shootout_win),
            null
        ),
        3 * countif(not is_awarded_result)
    ) as points_capture_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or shots is not null),
            sum(if(is_awarded_result, null, shots)),
            null
        ),
        if(
            logical_and(is_awarded_result or (shots + shots_against) is not null),
            sum(if(is_awarded_result, null, shots + shots_against)),
            null
        )
    ) as shots_share_pct,
    safe_divide(
        if(
            logical_and(is_awarded_result or (shots_on_target - shots_on_target_against) is not null),
            sum(if(is_awarded_result, null, shots_on_target - shots_on_target_against)),
            null
        ),
        countif(not is_awarded_result)
    ) as shots_on_goal_difference_per_match
    -- end of generated metric sql
from phase_rows
group by
    team_sk,
    season_sk,
    league_sk,
    league_code,
    season_api_year
