{#
  base_apif__lineup_sheets reads each team's latest fetch, and an earlier fetch may lend it grid
  places; both are picked by ingest time. Returns every team whose sheet was stored twice at one
  ingest time in a match, where nothing says which fetch is newer.
#}

select
    league_code,
    fixture_id,
    team_id,
    raw_ingested_at,
    count(*) as fetches
from {{ ref('stg_apif__lineups') }}
where fixture_id is not null and team_id is not null
group by league_code, fixture_id, team_id, raw_ingested_at
having count(*) > 1
