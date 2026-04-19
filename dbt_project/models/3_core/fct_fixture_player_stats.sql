{{ config(materialized='table') }}

{#
    Per-appearance player statistics. The source payload wraps a single stats
    block in a one-element array (``$[0]``). API-Football ships a real typo at
    ``$.penalty.commited``; preserved here to match the source.
#}

with src as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        player_statistics_json,
        raw_ingested_at,
        row_number() over (
            partition by fixture_id, team_id, player_id
            order by raw_ingested_at desc
        ) as rn
    from {{ ref('stg_apif__d1_fixture_players') }}
    where
        fixture_id is not null
        and team_id is not null
        and player_id is not null
),

latest as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        raw_ingested_at,
        json_query(player_statistics_json, '$[0]') as stats_el
    from src
    where rn = 1
),

flattened as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        raw_ingested_at,
        safe_cast(json_value(stats_el, '$.games.minutes') as int64) as minutes_played,
        safe_cast(json_value(stats_el, '$.games.number') as int64) as shirt_number,
        json_value(stats_el, '$.games.position') as position_code,
        safe_cast(json_value(stats_el, '$.games.rating') as float64) as rating,
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
        safe_cast(json_value(stats_el, '$.penalty.saved') as int64) as penalty_saved
    from latest
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'league_code', 'team_id', 'player_id']) }}
        as fixture_player_stat_sk,
    cast(fixture_id as int64) as fixture_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'team_id']) }} as team_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'player_id']) }} as player_sk,
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
from flattened
