-- Qualifier fixtures used for WC26 pre-tournament form computation.
-- These come from supporting_leagues queries (e.g. UEFA WCQ, CONCACAF WCQ).
-- Nullable venue and round columns are not available in the form endpoint response.

with src as (
    select * from {{ ref('stg_apif__wc26_form_fixtures') }}
    where fixture_id is not null
)

select
    league_code,
    fixture_id,
    league_api_id,
    season,
    fixture_date,
    kickoff_datetime,
    cast(null as string) as kickoff_timezone,
    status_short,
    cast(null as string) as status_long,
    cast(null as int64) as status_elapsed,
    cast(null as string) as round_name,
    home_team_id,
    away_team_id,
    goals_home,
    goals_away,
    cast(null as string) as venue_id,
    cast(null as string) as venue_name,
    cast(null as string) as venue_city,
    raw_ingested_at
from src
qualify row_number() over (
    partition by fixture_id
    order by raw_ingested_at desc
) = 1
