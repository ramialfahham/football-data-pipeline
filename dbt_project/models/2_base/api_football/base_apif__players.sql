-- Player identity (global entity): one row per player_api_id, unioned from five sources
-- and deduplicated in a single pass that prefers the most authoritative NAMED source
-- (lowest source_priority) and then the most recent ingest:
--   priority 1 — /players endpoint (biographical attributes, most complete)
--   priority 2 — fixture player stats (match appearances)
--   priority 3 — fixture events (broadest appearance coverage)
--   priority 4 — the assisting player of a fixture event
--   priority 5 — the match line-ups (a bench player who never came on)
-- Identity only — no league_code, no team/season affiliation: a player is one entity
-- across competitions, and "which team/season" lives in dim_player_team_season_mapping
-- and the facts, not here. Feeds dim_player 1:1. Grain: player_api_id.
with players_src as (
    select
        safe_cast(player_id as int64) as player_api_id,
        player_name,
        player_firstname as player_first_name,
        player_lastname as player_last_name,
        birth_date as player_birth_date,
        nationality as player_nationality,
        player_photo_url,
        raw_ingested_at,
        1 as source_priority
    from {{ ref('stg_apif__players') }}
    where player_id is not null
),

-- Match-appearance fallback: players seen in fixture player stats but absent from /players.
-- Only id, name and photo are known from this source.
fixture_players_src as (
    select
        player_id as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        player_photo_url,
        raw_ingested_at,
        2 as source_priority
    from {{ ref('stg_apif__fixture_players') }}
    where player_id is not null and player_id != 0
),

-- Event fallback: players seen in match events (broader than player stats), no photo.
fixture_events_src as (
    select
        safe_cast(player_id as int64) as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        cast(null as string) as player_photo_url,
        raw_ingested_at,
        3 as source_priority
    from {{ ref('base_apif__fixture_events') }}
    where
        safe_cast(player_id as int64) is not null
        and safe_cast(player_id as int64) != 0
),

-- The assisting player of a goal event, named as the events feed names the assist.
assist_events_src as (
    select
        assist_player_id as player_api_id,
        assist_player_name as player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        cast(null as string) as player_photo_url,
        raw_ingested_at,
        4 as source_priority
    from {{ ref('base_apif__fixture_events') }}
    where
        assist_player_id is not null
        and assist_player_id != 0
),

lineups_src as (
    select
        player_id as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        cast(null as string) as player_photo_url,
        raw_ingested_at,
        5 as source_priority
    from {{ ref('base_apif__lineups') }}
),

src as (
    select * from players_src
    union all
    select * from fixture_players_src
    union all
    select * from fixture_events_src
    union all
    select * from assist_events_src
    union all
    select * from lineups_src
)

select
    player_api_id,
    player_name,
    player_first_name,
    player_last_name,
    player_birth_date,
    player_nationality,
    player_photo_url,
    raw_ingested_at
from src
qualify row_number() over (
    partition by player_api_id
    order by
        source_priority asc,
        raw_ingested_at desc
) = 1
