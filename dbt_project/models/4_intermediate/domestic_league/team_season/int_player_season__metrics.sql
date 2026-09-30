{#
  Canonical per (player, competition-season) aggregate over all finished matches — the SINGLE player-season
  rollup consumed by mart_player_profile and mart_leaderboards (#480 consolidation; mart_player_season was
  retired with the leaderboards consolidation).

  Grain: (player_sk, season_sk) — one row per player per competition-season (season_sk encodes the
  competition). team_sk = the club of the player's last finished match that competition-season.

  The window is the player's competition-season, at every club he played for in it. Every metric is its
  catalogue formula over the window's leg rows, written by scripts/generate_metric_sql.py, and is NULL when
  the window lacks an input: a player row with a blank the provider did not count, or a match of one of his
  clubs with no player data at all. A ratio is never composed from pre-summed parts.
#}

with legs as (
    select * from {{ ref('int_legs__player_match') }}
),

-- A team match with no player data at all: nobody knows who played or what they did, so every player
-- metric of that team is blank for any window that contains it. Awarded results are no match played.
team_seasons_without_player_data as (
    select distinct
        tm.team_sk,
        tm.season_sk
    from {{ ref('int_legs__team_match') }} as tm
    left join {{ ref('int_legs__team_from_players') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
    where not tm.is_awarded_result and tp.fixture_sk is null
),

window_rows as (
    select
        legs.*,
        uncovered.team_sk is null as window_is_complete
    from legs
    left join team_seasons_without_player_data as uncovered
        on legs.team_sk = uncovered.team_sk and legs.season_sk = uncovered.season_sk
)

select
    player_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    array_agg(team_sk ignore nulls order by kickoff_datetime desc, team_sk desc limit 1)[safe_offset(0)]
        as team_sk,
    if(logical_and(window_is_complete and minutes is not null), countif(minutes > 0), null) as appearances,
    if(logical_and(window_is_complete and minutes is not null), countif(is_starter), null) as starts,
    if(
        logical_and(window_is_complete and minutes is not null),
        countif(coalesce(is_substitute, false) and minutes > 0),
        null
    ) as substitute_appearances,
    if(logical_and(window_is_complete and minutes is not null), sum(minutes), null) as minutes,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
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
    if(logical_and(window_is_complete and passes_key is not null), sum(passes_key), null) as passes_key_player,
    if(
        logical_and(window_is_complete and passes_accurate is not null),
        sum(passes_accurate),
        null
    ) as passes_accurate_player,
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
    if(
        logical_and(window_is_complete and dribbles_against is not null),
        sum(dribbles_against),
        null
    ) as dribbles_past_player,
    if(logical_and(window_is_complete and offsides is not null), sum(offsides), null) as offsides_player,
    if(logical_and(window_is_complete and cards_yellow is not null), sum(cards_yellow), null) as cards_yellow_player,
    if(logical_and(window_is_complete and cards_red is not null), sum(cards_red), null) as cards_red_player,
    if(logical_and(window_is_complete and penalties_won is not null), sum(penalties_won), null) as penalty_won_player,
    if(
        logical_and(window_is_complete and penalties_committed is not null),
        sum(penalties_committed),
        null
    ) as penalty_committed_player,
    if(logical_and(window_is_complete and saves is not null), sum(saves), null) as saves_player,
    if(logical_and(window_is_complete and goals_against is not null), sum(goals_against), null) as goals_against_player,
    if(
        logical_and(window_is_complete and (goals - goals_penalty) is not null),
        sum(goals - goals_penalty),
        null
    ) as goals_open_play_player,
    if(
        logical_and(window_is_complete and (goals + assists) is not null),
        sum(goals + assists),
        null
    ) as scorer_points_player,
    if(
        logical_and(window_is_complete and (tackles + interceptions + blocks) is not null),
        sum(tackles + interceptions + blocks),
        null
    ) as defensive_actions_player,
    if(
        logical_and(window_is_complete and (cards_yellow + cards_red) is not null),
        sum(cards_yellow + cards_red),
        null
    ) as cards_player,
    if(
        logical_and(window_is_complete and (saves + goals_against) is not null),
        sum(saves + goals_against),
        null
    ) as shots_on_goal_against_player,
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
    ) as saves_per90
    -- end of generated metric sql
from window_rows
group by player_sk, league_sk, season_sk, league_code, season_api_year
