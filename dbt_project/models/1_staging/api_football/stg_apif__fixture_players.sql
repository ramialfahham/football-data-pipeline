-- RAW_APIF_FIXTURE_DETAILS holds one merge-on-write row per (league_code, fixture_id): the loader
-- skip-fetches only finished fixtures missing data and deletes-on-retry (ingestion/api_football/
-- loads/batch_fixtures.py), so it is bounded yet carries many fixtures per league_code. Staging
-- reads ALL rows faithfully (NO latest-snapshot qualify — that would drop fixtures) and base
-- assembles current-per-fixture by entity-key dedup. See dbt_project/docs/layering.md §1_staging
-- (merge-on-write tables).
with src as (
    select *
    from {{ source('api_football', 'raw_apif_fixture_details') }}
),

team_rows as (
    select
        src.league_code,
        src.ingested_at as raw_ingested_at,
        team_block,
        safe_cast(json_value(src.payload, '$.fixture.id') as int64) as fixture_id
    from src,
        unnest(json_query_array(src.payload, '$.players')) as team_block
),

players as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_block,
        player_el
    from team_rows,
        unnest(
            json_query_array(team_block, '$.players')
        ) as player_el
),

flattened as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        safe_cast(json_value(team_block, '$.team.id') as int64) as team_id,
        json_value(team_block, '$.team.name') as team_name,
        safe_cast(json_value(player_el, '$.player.id') as int64) as player_id,
        json_value(player_el, '$.player.name') as player_name,
        json_value(player_el, '$.player.photo') as player_photo_url,
        safe_cast(json_value(stats_el, '$.games.minutes') as int64) as minutes_played,
        safe_cast(json_value(stats_el, '$.games.number') as int64) as shirt_number,
        json_value(stats_el, '$.games.position') as position_code,
        safe_cast(json_value(stats_el, '$.games.captain') as bool) as is_captain,
        safe_cast(json_value(stats_el, '$.games.substitute') as bool) as is_substitute,
        safe_cast(json_value(stats_el, '$.offsides') as int64) as offsides,
        safe_cast(json_value(stats_el, '$.shots.total') as int64) as shots_total,
        safe_cast(json_value(stats_el, '$.shots.on') as int64) as shots_on,
        safe_cast(json_value(stats_el, '$.goals.total') as int64) as goals_total,
        safe_cast(json_value(stats_el, '$.goals.conceded') as int64) as goals_conceded,
        safe_cast(json_value(stats_el, '$.goals.assists') as int64) as goals_assists,
        safe_cast(json_value(stats_el, '$.goals.saves') as int64) as goals_saves,
        safe_cast(json_value(stats_el, '$.passes.total') as int64) as passes_total,
        safe_cast(json_value(stats_el, '$.passes.key') as int64) as passes_key,
        safe_cast(
            regexp_replace(coalesce(json_value(stats_el, '$.passes.accuracy'), ''), r'%', '')
            as int64
        ) as passes_accuracy_percent,
        safe_cast(json_value(stats_el, '$.tackles.total') as int64) as tackles_total,
        safe_cast(json_value(stats_el, '$.tackles.blocks') as int64) as tackles_blocks,
        safe_cast(json_value(stats_el, '$.tackles.interceptions') as int64) as tackles_interceptions,
        safe_cast(json_value(stats_el, '$.duels.total') as int64) as duels_total,
        safe_cast(json_value(stats_el, '$.duels.won') as int64) as duels_won,
        safe_cast(json_value(stats_el, '$.dribbles.attempts') as int64) as dribbles_attempts,
        safe_cast(json_value(stats_el, '$.dribbles.success') as int64) as dribbles_success,
        safe_cast(json_value(stats_el, '$.dribbles.past') as int64) as dribbles_past,
        safe_cast(json_value(stats_el, '$.fouls.drawn') as int64) as fouls_drawn,
        safe_cast(json_value(stats_el, '$.fouls.committed') as int64) as fouls_committed,
        safe_cast(json_value(stats_el, '$.cards.yellow') as int64) as cards_yellow,
        safe_cast(json_value(stats_el, '$.cards.red') as int64) as cards_red,
        safe_cast(json_value(stats_el, '$.penalty.won') as int64) as penalty_won,
        safe_cast(json_value(stats_el, '$.penalty.commited') as int64) as penalty_committed,
        safe_cast(json_value(stats_el, '$.penalty.scored') as int64) as penalty_scored,
        safe_cast(json_value(stats_el, '$.penalty.missed') as int64) as penalty_missed,
        safe_cast(json_value(stats_el, '$.penalty.saved') as int64) as penalty_saved,
        to_json_string(player_el) as source_json
    from players
    left join unnest([json_query(player_el, '$.statistics[0]')]) as stats_el on true
)

select
    league_code,
    raw_ingested_at,
    fixture_id,
    team_id,
    team_name,
    player_id,
    player_name,
    player_photo_url,
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
    source_json
from flattened
