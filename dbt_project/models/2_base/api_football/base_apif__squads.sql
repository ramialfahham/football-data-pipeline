{#
  The provider's current squad lists: which player a team lists in a competition, on the latest
  snapshot. Grain: (league_code, team_api_id, player_api_id).
#}

with src as (
    select
        * except (player_id),
        {{ player_id_override('player_id') }} as player_id
    from {{ ref('stg_apif__squads') }}
    where team_id is not null and player_id is not null
)

select
    league_code,
    team_id as team_api_id,
    player_id as player_api_id,
    max(raw_ingested_at) as raw_ingested_at
from src
group by league_code, team_id, player_id
