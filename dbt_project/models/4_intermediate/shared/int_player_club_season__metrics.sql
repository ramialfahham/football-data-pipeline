{#
  Canonical per (player, CLUB, competition-season) aggregate over all finished matches — the finest-grain
  player rollup (#480 §8.3). Where int_player_season__metrics pools a whole competition-season, this keeps
  the club axis: a player with a mid-season transfer gets one honest row per club (not the last-club
  collapse). mart_player_career (the per-club career log) reads it.

  Grain: (player_sk, team_sk, season_sk) — season_sk encodes the competition, so this row is one player,
  at one club, in one competition-season. league_sk / league_code / season_api_year are carried for
  downstream slicing (each is functionally determined by season_sk).

  The window is the club's competition-season. Every metric is its catalogue formula over the window's leg
  rows, written by scripts/generate_metric_sql.py, and is NULL when the window lacks an input: a player row
  with a blank the provider did not count, or a club match with no player data at all.
  last_kickoff_at carries the club's latest kickoff so the competition-season model can reproduce the
  "last club that season" stamp.
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
    {{ dbt_utils.generate_surrogate_key(['player_sk', 'team_sk', 'season_sk']) }}
        as player_club_season_sk,
    player_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    max(kickoff_datetime) as last_kickoff_at,
    -- An appearance requires PITCH TIME: the provider lists the whole matchday squad, so an unused
    -- substitute arrives as a row with no minutes. Squad members who never played keep their row.
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
    safe_divide(
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null),
        if(logical_and(window_is_complete and (minutes > 0) is not null), countif(minutes > 0), null)
    ) as minutes_per_appearance
    -- end of generated metric sql
from window_rows
group by player_sk, team_sk, league_sk, season_sk, league_code, season_api_year
