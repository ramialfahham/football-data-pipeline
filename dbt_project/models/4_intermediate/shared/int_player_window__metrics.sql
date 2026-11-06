{#
  A player's metrics over each window of the page: every club competition of this season, of last
  season, and the nation's current competitions. Every metric is its catalogue formula over the
  window's leg rows, written by scripts/generate_metric_sql.py by the rules in
  models/docs/metric_rules.md. The window follows the player across clubs. A window with no match
  of the player has no row.

  Grain: (player_sk, window_type).
#}

with window_seasons as (
    select * from {{ ref('int_player_page__window_seasons') }}
),

window_legs as (
    select
        legs.*,
        w.window_type
    from window_seasons as w
    inner join {{ ref('int_legs__player_match') }} as legs
        on
            w.player_sk = legs.player_sk
            and w.season_sk = legs.season_sk
            and (w.team_sk is null or w.team_sk = legs.team_sk)
),

without_player_data as (
    {{ team_seasons_without_player_data() }}
),

window_teams as (
    select distinct
        player_sk,
        window_type,
        team_sk
    from window_legs
),

-- Any competition of the window counts, also one the player did not play in: the team's match with
-- no player data may be one the player played.
incomplete_windows as (
    select distinct
        t.player_sk,
        t.window_type
    from window_teams as t
    inner join window_seasons as w
        on t.player_sk = w.player_sk and t.window_type = w.window_type
    inner join without_player_data as u
        on t.team_sk = u.team_sk and w.season_sk = u.season_sk
),

window_rows as (
    select
        l.*,
        i.player_sk is null as window_is_complete
    from window_legs as l
    left join incomplete_windows as i
        on l.player_sk = i.player_sk and l.window_type = i.window_type
)

select
    player_sk,
    window_type,
    if(logical_and(window_is_complete and minutes is not null), sum(minutes), null) as minutes,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
    if(logical_and(window_is_complete and (minutes > 0) is not null), countif(minutes > 0), null) as appearances,
    if(logical_and(window_is_complete and goals is not null), sum(goals), null) as goals_player,
    if(logical_and(window_is_complete and goals_penalty is not null), sum(goals_penalty), null) as goals_penalty_player,
    if(logical_and(window_is_complete and assists is not null), sum(assists), null) as assists_player,
    if(logical_and(window_is_complete and shots is not null), sum(shots), null) as shots_player,
    if(
        logical_and(window_is_complete and shots_on_target is not null),
        sum(shots_on_target),
        null
    ) as shots_on_goal_player,
    if(logical_and(window_is_complete and passes is not null), sum(passes), null) as passes_player,
    if(
        logical_and(window_is_complete and passes_accurate is not null),
        sum(passes_accurate),
        null
    ) as passes_accurate_player,
    if(logical_and(window_is_complete and passes_key is not null), sum(passes_key), null) as passes_key_player,
    if(logical_and(window_is_complete and tackles is not null), sum(tackles), null) as tackles_player,
    if(logical_and(window_is_complete and interceptions is not null), sum(interceptions), null) as interceptions_player,
    if(logical_and(window_is_complete and blocks is not null), sum(blocks), null) as blocks_player,
    if(logical_and(window_is_complete and duels is not null), sum(duels), null) as duels_player,
    if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null) as duels_won_player,
    if(logical_and(window_is_complete and dribbles is not null), sum(dribbles), null) as dribbles_attempts_player,
    if(
        logical_and(window_is_complete and dribbles_success is not null),
        sum(dribbles_success),
        null
    ) as dribbles_success_player,
    if(logical_and(window_is_complete and saves is not null), sum(saves), null) as saves_player,
    if(logical_and(window_is_complete and goals_against is not null), sum(goals_against), null) as goals_against_player,
    if(logical_and(window_is_complete and cards_yellow is not null), sum(cards_yellow), null) as cards_yellow_player,
    if(logical_and(window_is_complete and cards_red is not null), sum(cards_red), null) as cards_red_player,
    safe_divide(
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null),
        if(logical_and(window_is_complete and (minutes > 0) is not null), countif(minutes > 0), null)
    ) as minutes_per_appearance,
    safe_divide(
        if(logical_and(window_is_complete and passes_accurate is not null), sum(passes_accurate), null),
        if(logical_and(window_is_complete and passes is not null), sum(passes), null)
    ) as passes_accuracy_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null),
        if(logical_and(window_is_complete and duels is not null), sum(duels), null)
    ) as duels_won_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and dribbles_success is not null), sum(dribbles_success), null),
        if(logical_and(window_is_complete and dribbles is not null), sum(dribbles), null)
    ) as dribbles_success_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and saves is not null), sum(saves), null),
        if(logical_and(window_is_complete and (saves + goals_against) is not null), sum(saves + goals_against), null)
    ) as saves_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and (goals - goals_penalty) is not null), sum(goals - goals_penalty), null),
        if(logical_and(window_is_complete and shots_on_target is not null), sum(shots_on_target), null)
    ) as finishing_efficiency_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and shots_on_target is not null), sum(shots_on_target), null),
        if(logical_and(window_is_complete and shots is not null), sum(shots), null)
    ) as shots_on_goal_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and goals is not null), sum(goals), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as goals_per90,
    safe_divide(
        if(logical_and(window_is_complete and assists is not null), sum(assists), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as assists_per90,
    safe_divide(
        if(logical_and(window_is_complete and (goals + assists) is not null), sum(goals + assists), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as scorer_points_per90,
    safe_divide(
        if(logical_and(window_is_complete and shots_on_target is not null), sum(shots_on_target), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as shots_on_goal_per90,
    safe_divide(
        if(logical_and(window_is_complete and passes_key is not null), sum(passes_key), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as passes_key_per90,
    safe_divide(
        if(logical_and(window_is_complete and dribbles_success is not null), sum(dribbles_success), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as dribbles_success_per90,
    safe_divide(
        if(logical_and(window_is_complete and passes is not null), sum(passes), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as passes_per90,
    safe_divide(
        if(logical_and(window_is_complete and tackles is not null), sum(tackles), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as tackles_per90,
    safe_divide(
        if(logical_and(window_is_complete and interceptions is not null), sum(interceptions), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as interceptions_per90,
    safe_divide(
        if(logical_and(window_is_complete and blocks is not null), sum(blocks), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as blocks_per90,
    safe_divide(
        if(
            logical_and(window_is_complete and (tackles + interceptions + blocks) is not null),
            sum(tackles + interceptions + blocks),
            null
        ) * 90,
        if(
            logical_and(window_is_complete and minutes is not null),
            sum(minutes),
            null
        )
    ) as defensive_actions_per90,
    safe_divide(
        if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as duels_won_per90,
    safe_divide(
        if(logical_and(window_is_complete and saves is not null), sum(saves), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as saves_per90,
    safe_divide(
        if(
            logical_and(
                window_is_complete
                and (passes + shots + dribbles + tackles + interceptions + blocks + saves) is not null
            ),
            sum(passes + shots + dribbles + tackles + interceptions + blocks + saves),
            null
        ) * 90,
        if(
            logical_and(
                window_is_complete
                and minutes is not null
            ),
            sum(minutes),
            null
        )
    ) as ball_actions_per90,
    safe_divide(
        if(logical_and(window_is_complete and shots is not null), sum(shots), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as shots_per90,
    safe_divide(
        if(logical_and(window_is_complete and fouls is not null), sum(fouls), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as fouls_per90,
    safe_divide(
        if(logical_and(window_is_complete and offsides is not null), sum(offsides), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as offsides_per90,
    safe_divide(
        if(logical_and(window_is_complete and goals_against is not null), sum(goals_against), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as goals_against_per90
    -- end of generated metric sql
from window_rows
group by player_sk, window_type
