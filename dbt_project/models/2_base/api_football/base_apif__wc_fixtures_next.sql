with src as (
    select * from {{ ref('stg_apif__wc_fixtures_next') }}
    where fixture_id is not null
)

select
    league_code,
    fixture_id,
    league_api_id,
    season,
    fixture_date,
    kickoff_datetime,
    kickoff_timezone,
    status_short,
    status_long,
    status_elapsed,
    round_name,
    home_team_id,
    away_team_id,
    goals_home,
    goals_away,
    venue_id,
    venue_name,
    venue_city,
    raw_ingested_at
from src
qualify row_number() over (
    partition by fixture_id
    order by raw_ingested_at desc
) = 1
