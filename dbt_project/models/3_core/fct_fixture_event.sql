{#
    One row per match event (goals, cards, substitutions, VAR decisions) across all
    onboarded competitions. Grain: (league_code, fixture_id, event_index) — event_index
    is the zero-based array position from the API-Football /fixtures/events response.
    API-Football does not emit event IDs; array position is the only stable unique
    identifier within a fixture's event list. A goal from fixture_goal_corrections stands
    at event_index 10000 plus its place in the match.
#}

with src as (
    select * from {{ ref('base_apif__fixture_events') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'event_index']) }} as event_sk,
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
    -- 0 is the API placeholder for "no player"; keep the event but null the FK so it
    -- does not point at a non-existent dim_player row (relationship tests ignore nulls).
    nullif(cast(player_id as int64), 0) as player_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    player_id as player_api_id,
    event_index,
    minute_elapsed,
    minute_extra,
    event_type,
    event_detail,
    event_comments,
    team_name as team_name_snapshot,
    player_name as player_name_snapshot,
    assist_player_name,
    nullif(cast(assist_player_id as int64), 0) as assist_player_sk,
    assist_player_id as assist_player_api_id,
    is_goal,
    is_own_goal,
    is_shootout_kick,
    goal_correction_source,
    src.raw_ingested_at
from src
