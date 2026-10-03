{#
  W1 momentum builder — player.

  For each upcoming fixture side, the metrics of every player who appeared in the side's window legs. The
  window selection is NOT re-derived here — it is consumed from the shared int_team_momentum_window model
  (extracted in #323), the SAME selection the team aggregate (int_team_momentum__metrics) and the
  drill-down list (mart_team_momentum_window) use. This keeps the player top-players strip and the team
  form panel on ONE window and prevents drift (#484).

  The window is carried through from int_team_momentum_window; window_type names it.

  Grain: (upcoming_fixture_sk, team_sk, player_sk).

  A player absent from some of the window legs contributes stats only for the matches they appeared
  in — honest absence, not zero. games_in_window is the player's appearance count within the side's
  window (0..5 for last_5, uncapped for tournament windows), not the team window size. It counts legs
  the player actually PLAYED (minutes > 0), so 0 is legitimate: named in the matchday squad for the
  window's legs but never brought on.

  Every metric is its catalogue formula over the window's leg rows, written by
  scripts/generate_metric_sql.py by the rules in models/docs/metric_rules.md.
#}

with window_legs as (
    select
        upcoming_fixture_sk,
        team_sk,
        season_api_year,
        entity_type,
        window_type,
        leg_fixture_sk
    from {{ ref('int_team_momentum_window') }}
),

-- A team match with no player data at all: nobody knows who played or what they did, so every player
-- metric of that team is blank for any window that contains it. Awarded results are no match played.
team_matches_without_player_data as (
    select
        tm.fixture_sk,
        tm.team_sk
    from {{ ref('int_legs__team_match') }} as tm
    left join {{ ref('int_legs__team_from_players') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
    where not tm.is_awarded_result and tp.fixture_sk is null
),

window_completeness as (
    select
        wl.upcoming_fixture_sk,
        wl.team_sk,
        logical_and(uncovered.fixture_sk is null) as window_is_complete
    from window_legs as wl
    left join team_matches_without_player_data as uncovered
        on wl.leg_fixture_sk = uncovered.fixture_sk and wl.team_sk = uncovered.team_sk
    group by wl.upcoming_fixture_sk, wl.team_sk
),

window_rows as (
    select
        p.* except (season_api_year, entity_type),
        wl.upcoming_fixture_sk,
        wl.season_api_year,
        wl.entity_type,
        wl.window_type,
        wc.window_is_complete
    from window_legs as wl
    inner join {{ ref('int_legs__player_match') }} as p
        on
            wl.leg_fixture_sk = p.fixture_sk
            and wl.team_sk = p.team_sk
    inner join window_completeness as wc
        on wl.upcoming_fixture_sk = wc.upcoming_fixture_sk and wl.team_sk = wc.team_sk
)

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    season_api_year,
    entity_type,
    window_type,
    if(logical_and(window_is_complete and minutes is not null), countif(minutes > 0), null) as games_in_window,
    any_value(position_code) as position_code,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
    if(logical_and(window_is_complete and goals is not null), sum(goals), null) as goals_player,
    if(logical_and(window_is_complete and assists is not null), sum(assists), null) as assists_player,
    if(logical_and(window_is_complete and goals_against is not null), sum(goals_against), null) as goals_against_player,
    if(logical_and(window_is_complete and saves is not null), sum(saves), null) as saves_player,
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
    if(logical_and(window_is_complete and blocks is not null), sum(blocks), null) as blocks_player,
    if(logical_and(window_is_complete and interceptions is not null), sum(interceptions), null) as interceptions_player,
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
    safe_divide(
        if(logical_and(window_is_complete and saves is not null), sum(saves), null),
        if(logical_and(window_is_complete and (saves + goals_against) is not null), sum(saves + goals_against), null)
    ) as saves_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and dribbles_success is not null), sum(dribbles_success), null),
        if(logical_and(window_is_complete and dribbles is not null), sum(dribbles), null)
    ) as dribbles_success_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and passes_accurate is not null), sum(passes_accurate), null),
        if(logical_and(window_is_complete and passes is not null), sum(passes), null)
    ) as passes_accuracy_player_pct,
    safe_divide(
        if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null),
        if(logical_and(window_is_complete and duels is not null), sum(duels), null)
    ) as duels_won_player_pct
    -- end of generated metric sql
from window_rows
group by
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    season_api_year,
    entity_type,
    window_type
