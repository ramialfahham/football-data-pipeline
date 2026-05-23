-- Unified fixture-player rows across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Output grain: (league_code, fixture_id, team_id, player_id).
{% set league_codes = var('active_competition_league_codes') %}

with src as (

    {% for lc in league_codes %}
    {% if not loop.first %}

    union all

    {% endif %}
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
    from {{ ref('stg_apif__' ~ lc | lower ~ '_fixture_players') }}
    where
        fixture_id is not null
        and team_id is not null
        and player_id is not null

    {% endfor %}

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
    partition by league_code, fixture_id, team_id, player_id
    order by raw_ingested_at desc
) = 1
