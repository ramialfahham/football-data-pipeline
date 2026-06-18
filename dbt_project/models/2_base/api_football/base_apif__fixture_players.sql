with src as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        minutes_played,
        shirt_number,
        position_code,
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
        tackles_total,
        tackles_blocks,
        tackles_interceptions,
        duels_total,
        duels_won,
        dribbles_attempts,
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
        raw_ingested_at,
        -- Clamp impossible source values to their valid domain (the API has reported
        -- pass accuracy up to 191% and dribble success > attempts). Keeps derived
        -- ratios in [0,1]; least() preserves NULL.
        least(passes_accuracy_percent, 100) as passes_accuracy_percent,
        least(dribbles_success, dribbles_attempts) as dribbles_success
    from {{ ref('stg_apif__fixture_players') }}
    where
        fixture_id is not null
        and team_id is not null
        and player_id is not null
        -- player_id = 0 is the API placeholder for an unknown player (no real id);
        -- it is not a real player and produces phantom cross-team duplicate legs.
        and player_id != 0
)

select
    league_code,
    fixture_id,
    team_id,
    player_id,
    minutes_played,
    shirt_number,
    position_code,
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
    partition by league_code, fixture_id, team_id, player_id
    order by raw_ingested_at desc
) = 1
