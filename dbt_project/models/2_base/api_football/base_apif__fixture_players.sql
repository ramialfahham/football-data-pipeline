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
        goals_against,
        goals_assists,
        saves,
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
),

-- Fixture participants (home/away team ids), used to evaluate the reattribute_if_cohabiting
-- override condition below. base_apif__fixtures_next grain is one row per fixture_id. Only
-- fixtures whose two participants are BOTH known are kept, so the IN / NOT IN participant checks
-- in the reattribute join never hit the NOT IN (value, NULL) -> UNKNOWN trap (a fixture with a
-- missing participant id is a separate defect; the override conservatively does not fire there).
fixture_participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        home_team_id is not null
        and away_team_id is not null
),

-- Hand-curated corrections for known provider team-id defects, from
-- seeds/fixture_team_id_overrides.csv. `alias` = unconditional duplicate-id replacement (one club
-- under two provider ids); `reattribute_if_cohabiting` = replace only when the correct id is a
-- fixture participant and the wrong id is not (a mis-attribution between two DISTINCT clubs, so a
-- club's own legitimate lineups are never touched). Same seed and same two modes the events model
-- has used since #526; it was simply never wired to this feed, which is how one stub team block --
-- id 22722, name null -- put a lineup under a club that does not exist and stopped the nightly.
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode
    from {{ ref('fixture_team_id_overrides') }}
),

-- Corrected BEFORE the qualify below, not after, because both of its window functions partition on
-- team_id: the dedup key, which the model's uniqueness test covers, and the cross-team collision
-- guard. The guard now sees corrected ids, which is the intended direction -- a player appearing
-- under both a wrong id and its correct one was never two players, and dropping that leg as
-- unattributable would discard a real appearance.
corrected as (
    select
        src.* except (team_id),
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            src.team_id
        ) as team_id
    from src
    left join overrides as alias_override
        on
            src.team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on src.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            src.team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
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
    goals_against,
    goals_assists,
    saves,
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
from corrected
qualify
    row_number() over (
        partition by league_code, fixture_id, team_id, player_id
        order by raw_ingested_at desc
    ) = 1
    -- Drop cross-team id-collisions: the provider sometimes reuses one player_id for two
    -- different players in a fixture (one per team, e.g. AFCCL 2016 id 44061), so the id is
    -- unreliable and both legs are unattributable. Extends the player_id = 0 phantom-leg
    -- cleanup above to real-but-collided ids; keeps the (fixture, player) grain unique
    -- downstream (int_legs__player_match / mart_player_match_log).
    and min(team_id) over (partition by league_code, fixture_id, player_id)
    = max(team_id) over (partition by league_code, fixture_id, player_id)
