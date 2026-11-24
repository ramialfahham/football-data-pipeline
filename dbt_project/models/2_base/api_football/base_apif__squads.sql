{#
  The provider's current squad list of each team: the players its newest fetch carried, whichever
  league's row that fetch was written under. A team whose newest fetch found no player has none
  here, and an older list is not read in its place. Grain: (team_api_id, player_api_id).
  league_code is the league the newest fetch was written under, the smallest when two were written
  at the same instant.
#}

with fetched as (
    select
        {{ team_id_override('team_id') }} as team_id,
        raw_ingested_at
    from {{ ref('stg_apif__squads') }}
    where team_id is not null
),

newest as (
    select
        team_id,
        max(raw_ingested_at) as raw_ingested_at
    from fetched
    group by team_id
),

src as (
    select
        * except (player_id, team_id),
        {{ player_id_override('player_id') }} as player_id,
        {{ team_id_override('team_id') }} as team_id
    from {{ ref('stg_apif__squads') }}
    where team_id is not null and player_id is not null
)

select
    src.team_id as team_api_id,
    src.player_id as player_api_id,
    src.raw_ingested_at,
    min(src.league_code) as league_code
from src
inner join newest
    on src.team_id = newest.team_id and src.raw_ingested_at = newest.raw_ingested_at
group by src.team_id, src.player_id, src.raw_ingested_at
