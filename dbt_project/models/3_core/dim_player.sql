{{ config(materialized='table') }}

with src as (
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
        raw_ingested_at
    from {{ ref('stg_apif__d1_players') }}
    where player_id is not null
),

ranked as (
    select
        *,
        row_number() over (
            partition by league_code, player_api_id
            order by last_known_season_year desc, last_known_team_api_id desc, raw_ingested_at desc
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
