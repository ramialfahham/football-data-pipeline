{{ config(materialized='table') }}

with src as (
    select * from {{ ref('base_apif__fixture_players') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'league_code', 'team_id', 'player_id']) }}
        as fixture_player_stat_sk,
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
    cast(player_id as int64) as player_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    player_id as player_api_id,
    minutes_played,
    shirt_number,
    position_code,
    rating,
    is_captain,
    is_substitute,
    coalesce(minutes_played, 0) > 0 and not coalesce(is_substitute, false) as is_starter,
    offsides,
    shots_total,
    shots_on,
    goals_total,
    goals_conceded,
    goals_assists,
    goals_saves,
    passes_total,
    passes_key,
    passes_accuracy_percent,
    tackles_total,
    tackles_blocks,
    tackles_interceptions,
    duels_total,
    duels_won,
    dribbles_attempts,
    dribbles_success,
    dribbles_past,
    fouls_drawn,
    fouls_committed,
    cards_yellow,
    cards_red,
    penalty_won,
    penalty_committed,
    penalty_scored,
    penalty_missed,
    penalty_saved,
    raw_ingested_at
from src
