{{ config(materialized='table') }}

with stg_apif__bl1_players as (
    select * from {{ ref('stg_apif__bl1_players') }}
),

stg_apif__bl1_transfers as (
    select * from {{ ref('base_apif__bl1_transfers') }}
),

players_src as (
    select
        league_code,
        player_id as player_api_id,
        player_name,
        player_firstname as player_first_name,
        player_lastname as player_last_name,
        birth_date as player_birth_date,
        nationality as player_nationality,
        player_photo_url,
        team_id as last_known_team_api_id,
        season_year as last_known_season_year,
        raw_ingested_at,
        1 as source_priority
    from stg_apif__bl1_players
    where player_id is not null
),

transfers_src as (
    select
        league_code,
        player_id as player_api_id,
        player_name,
        cast(null as string) as player_first_name,
        cast(null as string) as player_last_name,
        cast(null as date) as player_birth_date,
        cast(null as string) as player_nationality,
        player_photo_url,
        cast(null as int64) as last_known_team_api_id,
        cast(null as int64) as last_known_season_year,
        raw_ingested_at,
        2 as source_priority
    from stg_apif__bl1_transfers
    where player_id is not null
),

src as (
    select * from players_src
    union all
    select * from transfers_src
),

ranked as (
    select
        *,
        row_number() over (
            partition by league_code, player_api_id
            order by
                source_priority asc,
                last_known_season_year desc,
                last_known_team_api_id desc,
                raw_ingested_at desc
        ) as rn
    from src
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'player_api_id']) }} as player_sk,
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
from ranked
where rn = 1
