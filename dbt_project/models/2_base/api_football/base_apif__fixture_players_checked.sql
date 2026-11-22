{#
  The rows of base_apif__fixture_players, with a player's goals withheld where
  base_apif__fixture_events_checked withholds him as the scorer of a goal that counts, and his
  assists where it withholds him as the assister. This is its own model because base_apif__lineups
  reads base_apif__fixture_players. The columns keep base_apif__fixture_players' order, which
  fct_fixture_player_stats unions by position. A line filed under a team that did not play the match
  carries team_needs_research, and fct_fixture_player_stats leaves it out.

  Grain: (league_code, fixture_id, team_id, player_id).
#}

with withheld_goals as (
    select
        events.league_code,
        events.fixture_id,
        events.player_id,
        events.assist_player_id,
        checked.assist_needs_research,
        checked.scorer_needs_research and not checked.is_own_goal as scorer_needs_research
    from {{ ref('base_apif__fixture_events') }} as events
    inner join {{ ref('base_apif__fixture_events_checked') }} as checked
        on
            events.league_code = checked.league_code
            and events.fixture_id = checked.fixture_id
            and events.event_index = checked.event_index
    where checked.is_goal and (checked.scorer_needs_research or checked.assist_needs_research)
),

withheld_roles as (
    select
        league_code,
        fixture_id,
        player_id,
        true as is_scorer,
        false as is_assister
    from withheld_goals
    where scorer_needs_research and player_id is not null
    union all
    select
        league_code,
        fixture_id,
        assist_player_id as player_id,
        false as is_scorer,
        true as is_assister
    from withheld_goals
    where assist_needs_research and assist_player_id is not null
),

withheld_players as (
    select
        league_code,
        fixture_id,
        player_id,
        logical_or(is_scorer) as scorer_withheld,
        logical_or(is_assister) as assister_withheld
    from withheld_roles
    group by league_code, fixture_id, player_id
),

participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
),

disputed_players as (
    {{ player_team_disputes(ref('base_apif__fixture_players'), ref('base_apif__fixture_events'), 'participants') }}
),

checked_players as (
    select
        players.*,
        {{ team_not_in_fixture('players.team_id', 'participants.home_team_id', 'participants.away_team_id') }}
            as team_needs_research,
        disputed_players.fixture_id is not null as player_team_needs_research,
        if(coalesce(withheld.scorer_withheld, false), null, players.goals) as checked_goals,
        if(coalesce(withheld.scorer_withheld, false), null, players.goals_penalty) as checked_goals_penalty,
        if(coalesce(withheld.scorer_withheld, false), null, players.penalties_scored) as checked_penalties_scored,
        if(coalesce(withheld.assister_withheld, false), null, players.assists) as checked_assists
    from {{ ref('base_apif__fixture_players') }} as players
    left join withheld_players as withheld
        on
            players.league_code = withheld.league_code
            and players.fixture_id = withheld.fixture_id
            and players.player_id = withheld.player_id
    left join participants
        on players.fixture_id = participants.fixture_id
    left join disputed_players
        on players.fixture_id = disputed_players.fixture_id and players.player_id = disputed_players.player_id
)

select
    league_code,
    fixture_id,
    team_id,
    player_id,
    minutes,
    shirt_number,
    position_code,
    is_captain,
    is_substitute,
    offsides,
    shots,
    shots_on_target,
    checked_goals as goals,
    checked_goals_penalty as goals_penalty,
    goals_against,
    goals_own_against,
    checked_assists as assists,
    saves,
    passes,
    passes_key,
    passes_accurate,
    tackles,
    blocks,
    interceptions,
    duels,
    duels_won,
    dribbles,
    dribbles_success,
    dribbles_against,
    fouls,
    fouls_against,
    cards_yellow,
    cards_red,
    penalties_won,
    penalties_committed,
    checked_penalties_scored as penalties_scored,
    penalties_missed,
    penalties_saved,
    raw_ingested_at,
    stat_corrections,
    team_needs_research,
    player_team_needs_research
from checked_players
