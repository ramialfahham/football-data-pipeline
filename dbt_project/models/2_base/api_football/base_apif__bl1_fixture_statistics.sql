with src as (
    select * from {{ ref('stg_apif__bl1_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
)

select
    league_code,
    fixture_id,
    team_id,
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
from src
qualify row_number() over (
    partition by fixture_id, team_id
    order by raw_ingested_at desc
) = 1
