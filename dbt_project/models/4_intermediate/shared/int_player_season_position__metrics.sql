{#
  Per (player, competition-season, POSITION) aggregate over all finished matches — the position-split
  sibling of int_player_season__metrics, built for the player competition benchmark (content_architecture
  §6). Where int_player_season__metrics pools the whole season, this splits a player's legs by the position
  he played that match (position_code, recorded at match time) and aggregates each role separately. A
  player who logged minutes in two positions gets two rows, each carrying the per-90 he produced IN that
  role — so a multi-position player is benchmarked honestly per position, and the minutes >= 270 floor
  applied downstream both qualifies and assigns the position.

  position_code G/D/M/F -> position_group GK/DEF/MID/ATT; non-canonical codes ('-'/'SUB'/null) are dropped
  (they cannot be assigned a position). Every metric is its catalogue formula over the window's leg rows,
  written by scripts/generate_metric_sql.py, so a single-position player's per-90 here equals his
  whole-season per-90 there. The window is complete only when every club he played for that
  competition-season has player data for every match, as on the whole-season surface.

  Grain: (player_sk, season_sk, position_group). No floor here — the benchmark engine/mart filter
  minutes >= 270. The 18 benchmark metrics (per-90 + rates) are listed in the player_benchmark_metrics()
  macro (shared with int_player_competition_benchmarks + mart_player_competition_benchmarks).
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

season_rows as (
    select
        legs.*,
        logical_and(uncovered.team_sk is null) over (partition by legs.player_sk, legs.season_sk)
            as window_is_complete
    from legs
    left join team_seasons_without_player_data as uncovered
        on legs.team_sk = uncovered.team_sk and legs.season_sk = uncovered.season_sk
),

window_rows as (
    select
        *,
        case position_code
            when 'G' then 'GK'
            when 'D' then 'DEF'
            when 'M' then 'MID'
            when 'F' then 'ATT'
        end as position_group
    from season_rows
    where position_code in ('G', 'D', 'M', 'F')
)

select
    player_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    position_group,
    -- pitch time required, same rule as int_player_club_season__metrics: the provider lists whole
    -- matchday squads, so an unused substitute is no appearance.
    if(logical_and(window_is_complete and minutes is not null), countif(minutes > 0), null) as appearances,
    if(logical_and(window_is_complete and minutes is not null), sum(minutes), null) as minutes,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
    if(logical_and(window_is_complete and goals is not null), sum(goals), null) as goals_player,
    if(logical_and(window_is_complete and goals_penalty is not null), sum(goals_penalty), null) as goals_penalty_player,
    if(logical_and(window_is_complete and assists is not null), sum(assists), null) as assists_player,
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
group by player_sk, league_sk, season_sk, league_code, season_api_year, position_group
