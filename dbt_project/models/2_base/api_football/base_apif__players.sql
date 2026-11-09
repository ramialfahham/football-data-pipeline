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
        {{ player_id_override('safe_cast(player_id as int64)') }} as player_api_id,
        player_name,
        player_firstname as player_first_name,
        player_lastname as player_last_name,
        {{ possible_birth_date('birth_date', 'raw_ingested_at') }} as player_birth_date,
        nationality as player_nationality,
        player_photo_url,
        raw_ingested_at,
        1 as source_priority,
        season_year as tie_recency
    from {{ ref('stg_apif__players') }}
    where player_id is not null
),

-- Match-appearance fallback: players seen in fixture player stats but absent from /players.
-- Only id, name and photo are known from this source.
fixture_players_src as (
    select
        {{ player_id_override('player_id') }} as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        player_photo_url,
        raw_ingested_at,
        2 as source_priority,
        fixture_id as tie_recency
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
        3 as source_priority,
        fixture_id as tie_recency
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
        4 as source_priority,
        fixture_id as tie_recency
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
        5 as source_priority,
        fixture_id as tie_recency
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
),

import_player_bio_corrections as (
    select * from {{ ref('player_bio_corrections') }}
),

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

-- Rows tied on source and ingest time can disagree: a player has one /players row per team and
-- season, all stamped by one batch. The order below settles every tie the same way on every build.
latest as (
    select
        player_api_id,
        player_name,
        player_first_name,
        player_last_name,
        player_birth_date,
        player_nationality,
        player_photo_url,
        raw_ingested_at,
        count(distinct player_birth_date) over (
            partition by player_api_id, source_priority, raw_ingested_at
        ) > 1 as has_conflicting_birth_date,
        count(distinct player_nationality) over (
            partition by player_api_id, source_priority, raw_ingested_at
        ) > 1 as has_conflicting_nationality
    from src
    qualify row_number() over (
        partition by player_api_id
        order by
            source_priority asc,
            raw_ingested_at desc,
            player_birth_date is null asc,
            player_nationality is null asc,
            tie_recency desc,
            player_birth_date asc,
            player_nationality asc,
            player_name asc,
            player_first_name asc,
            player_last_name asc,
            player_photo_url asc
    ) = 1
),

corrected as (
    select
        latest.player_api_id,
        latest.player_name,
        latest.player_first_name,
        latest.player_last_name,
        latest.player_photo_url,
        latest.raw_ingested_at,
        latest.has_conflicting_birth_date,
        latest.has_conflicting_nationality,
        safe_cast(
            {{ bio_correction('birth_date_fix', 'cast(latest.player_birth_date as string)') }} as date
        ) as player_birth_date,
        nullif(
            trim(
                coalesce(
                    nationality_overrides.country_name,
                    {{ bio_correction('nationality_fix', 'latest.player_nationality') }}
                )
            ),
            ''
        ) as player_nationality
    from latest
    left join import_player_bio_corrections as birth_date_fix
        on
            latest.player_api_id = birth_date_fix.player_api_id
            and birth_date_fix.corrected_field = 'player_birth_date'
    left join import_player_bio_corrections as nationality_fix
        on
            latest.player_api_id = nationality_fix.player_api_id
            and nationality_fix.corrected_field = 'player_nationality'
    -- the provider's exact string is the seed's key, garbled spellings included
    left join import_country_name_overrides as nationality_overrides
        on
            {{ bio_correction('nationality_fix', 'latest.player_nationality') }}
            = nationality_overrides.provider_country
)

select
    player_api_id,
    player_birth_date,
    player_photo_url,
    raw_ingested_at,
    has_conflicting_birth_date,
    has_conflicting_nationality,
    {{ repair_garbled_text('player_name') }} as player_name,
    {{ repair_garbled_text('player_first_name') }} as player_first_name,
    {{ repair_garbled_text('player_last_name') }} as player_last_name,
    {{ repair_garbled_text('player_nationality') }} as player_nationality
from corrected
