{{ config(materialized='table') }}

with base as (
    select * from {{ ref('base_apif__d1_fixture_statistics') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'league_code', 'team_id']) }}
        as fixture_team_stat_sk,
    cast(fixture_id as int64) as fixture_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'team_id']) }} as team_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    shots_on_goal,
    shots_off_goal,
    shots_total,
    shots_blocked,
    shots_inside_box,
    shots_outside_box,
    fouls,
    corner_kicks,
    offsides,
    ball_possession_percent,
    yellow_cards,
    red_cards,
    goalkeeper_saves,
    passes_total,
    passes_accurate,
    passes_accuracy_percent,
    raw_ingested_at
from base
