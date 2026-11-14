{#
  Canonical per (player, competition-season) aggregate over all finished matches — the SINGLE player-season
  rollup consumed by mart_player_profile and mart_leaderboards (#480 consolidation; mart_player_season was
  retired with the leaderboards consolidation).

  Grain: (player_sk, season_sk) — one row per player per competition-season (season_sk encodes the
  competition). team_sk = the club of the player's last finished match that competition-season.

  The window is the player's competition-season, at every club he played for in it. Every metric is its
  catalogue formula over the window's leg rows, written by scripts/generate_metric_sql.py by the rules in
  models/docs/metric_rules.md.
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
    left join {{ ref('int_legs__player_match') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
    where not tm.is_awarded_result and tp.fixture_sk is null
),

-- A match's midfield role counts when its team sheet is confirmed or researched.
role_matches as (
    select
        legs.player_sk,
        legs.season_sk,
        legs.season_api_year,
        legs.kickoff_datetime,
        lineups.midfield_role
    from legs
    inner join {{ ref('fct_fixture_lineup') }} as lineups
        on
            legs.fixture_sk = lineups.fixture_sk
            and legs.team_sk = lineups.team_sk
            and legs.player_sk = lineups.player_sk
    where lineups.midfield_role is not null and lineups.lineup_state in ('confirmed', 'researched')
),

-- His season role: the most frequent over that season's matches, then the role of his latest match,
-- then the code.
this_season_roles as (
    select
        player_sk,
        season_sk,
        midfield_role
    from role_matches
    group by player_sk, season_sk, midfield_role
    qualify row_number() over (
        partition by player_sk, season_sk
        order by count(*) desc, max(kickoff_datetime) desc, midfield_role asc
    ) = 1
),

player_seasons as (
    select distinct
        player_sk,
        season_sk,
        season_api_year
    from legs
),

-- Without one, his most frequent role over his matches in every other season; a tie goes to the
-- role of the nearest season, then of the earlier one.
other_season_roles as (
    select
        ps.player_sk,
        ps.season_sk,
        rm.midfield_role
    from player_seasons as ps
    inner join role_matches as rm
        on ps.player_sk = rm.player_sk and ps.season_sk != rm.season_sk
    group by ps.player_sk, ps.season_sk, rm.midfield_role
    qualify row_number() over (
        partition by ps.player_sk, ps.season_sk
        order by
            count(*) desc,
            min(
                abs(rm.season_api_year - ps.season_api_year) * 2
                + if(rm.season_api_year < ps.season_api_year, 0, 1)
            ) asc,
            rm.midfield_role asc
    ) = 1
),

window_rows as (
    select
        legs.*,
        coalesce(own.midfield_role, other.midfield_role) as season_midfield_role,
        case
            when own.midfield_role is not null then 'this_season'
            when other.midfield_role is not null then 'other_seasons'
        end as season_midfield_role_from,
        uncovered.team_sk is null as window_is_complete
    from legs
    left join team_seasons_without_player_data as uncovered
        on legs.team_sk = uncovered.team_sk and legs.season_sk = uncovered.season_sk
    left join this_season_roles as own
        on legs.player_sk = own.player_sk and legs.season_sk = own.season_sk
    left join other_season_roles as other
        on legs.player_sk = other.player_sk and legs.season_sk = other.season_sk
)

select
    player_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    array_agg(team_sk ignore nulls order by kickoff_datetime desc, team_sk desc limit 1)[safe_offset(0)]
        as team_sk,
    max(season_midfield_role) as midfield_role,
    max(season_midfield_role_from) as midfield_role_from,
    if(logical_and(window_is_complete and minutes is not null), countif(is_starter), null) as starts,
    if(
        logical_and(window_is_complete and minutes is not null),
        countif(coalesce(is_substitute, false) and minutes > 0),
        null
    ) as substitute_appearances,
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
    if(
        logical_and(
            window_is_complete and (passes + shots + dribbles + tackles + interceptions + blocks + saves) is not null
        ),
        sum(passes + shots + dribbles + tackles + interceptions + blocks + saves),
        null
    ) as ball_actions_player,
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
    ) as goals_against_per90,
    safe_divide(
        if(logical_and(window_is_complete and passes_accurate is not null), sum(passes_accurate), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as passes_accurate_per90,
    safe_divide(
        if(logical_and(window_is_complete and dribbles is not null), sum(dribbles), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as dribbles_attempts_per90,
    safe_divide(
        if(logical_and(window_is_complete and duels is not null), sum(duels), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as duels_per90,
    safe_divide(
        if(logical_and(window_is_complete and dribbles_against is not null), sum(dribbles_against), null) * 90,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
    ) as dribbles_past_per90
    -- end of generated metric sql
from window_rows
group by player_sk, league_sk, season_sk, league_code, season_api_year
