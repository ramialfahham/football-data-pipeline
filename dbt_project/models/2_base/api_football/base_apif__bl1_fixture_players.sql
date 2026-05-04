with src as (
    select * from {{ ref('stg_apif__bl1_fixture_players') }}
    where
        fixture_id is not null
        and team_id is not null
        and player_id is not null
)

select
    league_code,
    fixture_id,
    team_id,
    player_id,
    minutes_played,
    shirt_number,
    position_code,
    rating,
    is_captain,
    is_substitute,
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
qualify row_number() over (
    partition by fixture_id, team_id, player_id
    order by raw_ingested_at desc
) = 1
