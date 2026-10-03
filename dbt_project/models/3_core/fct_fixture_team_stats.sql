with src as (
    select * from {{ ref('base_apif__fixture_statistics') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'league_code', 'team_id']) }}
        as fixture_team_stat_sk,
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    has_stat_line,
    shots_on_target,
    shots_off_target,
    shots,
    shots_blocked,
    shots_inside_box,
    shots_outside_box,
    fouls,
    corners,
    offsides,
    possession_pct,
    cards_yellow,
    cards_red,
    saves,
    passes,
    passes_accurate,
    goals_penalty,
    goals_own,
    src.raw_ingested_at
from src
