-- Rostered player↔team↔season affiliation: one row per player per team per season,
-- taken directly from the /players squad source (stg_apif__players). This captures
-- squad members who never played a match — which no fact can express — so membership
-- is single-source ROSTERED, never derived from facts.
-- Grain: (league_code, player_id, team_id, season_year). league_code flows through.
with src as (
    select * from {{ ref('stg_apif__players') }}
)

select
    league_code,
    player_id,
    team_id,
    season_year,
    raw_ingested_at
from src
where
    player_id is not null
    and team_id is not null
    and season_year is not null
qualify row_number() over (
    partition by league_code, player_id, team_id, season_year
    order by raw_ingested_at desc
) = 1
