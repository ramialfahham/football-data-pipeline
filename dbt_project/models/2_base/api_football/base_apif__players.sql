-- Player identity, unioned from three sources (lowest source_priority wins per
-- (league_code, player_api_id)):
--   priority 1 — /players endpoint (biographical attributes, most complete)
--   priority 2 — fixture player stats (match appearances)
--   priority 3 — fixture events (broadest appearance coverage)
-- Output grain: (league_code, player_api_id) — one row per player per league.
-- base_apif__players_global deduplicates further to one row per player_api_id.
with players_src as (
    select
        league_code,
        safe_cast(player_id as int64) as player_api_id,
        player_name,
        player_firstname as player_first_name,
        player_lastname as player_last_name,
        birth_date as player_birth_date,
        nationality as player_nationality,
        player_photo_url,
        safe_cast(team_id as int64) as last_known_team_api_id,
        safe_cast(season_year as int64) as last_known_season_year,
        raw_ingested_at,
        1 as source_priority
    from {{ ref('stg_apif__players') }}
    where player_id is not null
),

-- Match-appearance fallback: players seen in fixture player stats but absent from the
-- above. Completes dim_player so player-stat / leg facts have valid FKs. Only id, name,
-- photo and the team they appeared for are known from this source.
fixture_players_src as (
    select
        league_code,
        player_id as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        player_photo_url,
        team_id as last_known_team_api_id,
        cast(null as int64) as last_known_season_year,
        raw_ingested_at,
        2 as source_priority
    from {{ ref('stg_apif__fixture_players') }}
    where player_id is not null and player_id != 0
),

-- Event fallback: players seen in match events (broader coverage than player stats)
-- but absent from the above. The events payload carries no photo.
fixture_events_src as (
    select
        league_code,
        safe_cast(player_id as int64) as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        cast(null as string) as player_photo_url,
        cast(null as int64) as last_known_team_api_id,
        cast(null as int64) as last_known_season_year,
        raw_ingested_at,
        3 as source_priority
    from {{ ref('base_apif__fixture_events') }}
    where
        safe_cast(player_id as int64) is not null
        and safe_cast(player_id as int64) != 0
),

src as (
    select * from players_src
    union all
    select * from fixture_players_src
    union all
    select * from fixture_events_src
)

select
    league_code,
    player_api_id,
    player_name,
    player_first_name,
    player_last_name,
    player_birth_date,
    player_nationality,
    player_photo_url,
    last_known_team_api_id,
    last_known_season_year,
    raw_ingested_at
from src
qualify row_number() over (
    partition by league_code, player_api_id
    order by
        source_priority asc,
        last_known_season_year desc nulls last,
        last_known_team_api_id desc nulls last,
        raw_ingested_at desc
) = 1
