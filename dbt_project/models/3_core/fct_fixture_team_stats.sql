{{
    config(
        materialized='incremental',
        unique_key='fixture_team_stat_sk',
        on_schema_change='sync_all_columns'
    )
}}

with base as (
    select * from {{ ref('base_apif__fixture_statistics') }}
),

src as (
    select *
    from base
    {% if is_incremental() %}
    where base.raw_ingested_at > (select max(tgt.raw_ingested_at) from {{ this }} as tgt)
    {% endif %}
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'league_code', 'team_id']) }}
        as fixture_team_stat_sk,
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
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
    src.raw_ingested_at
from src
