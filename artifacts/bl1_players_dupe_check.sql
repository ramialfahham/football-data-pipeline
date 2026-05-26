-- Find the 41 duplicate (league_code, team_id, season_year, player_id) rows in stg_apif__bl1_players
-- and show how many raw payloads exist for the affected (team_id, season_year) combos

with stg as (
    select
        league_code,
        team_id,
        season_year,
        player_id,
        player_name,
        raw_ingested_at,
        count(*) over (partition by league_code, team_id, season_year, player_id) as n_dupes
    from `football-data-pipeline-gcp.staging.stg_apif__bl1_players`
),

dupes as (
    select * from stg where n_dupes > 1
),

-- How many distinct raw_ingested_at values for each duped (team, season) combo?
raw_payload_counts as (
    select
        team_id,
        season_year,
        count(distinct raw_ingested_at) as n_distinct_ingested_at,
        min(raw_ingested_at) as earliest_ingest,
        max(raw_ingested_at) as latest_ingest
    from dupes
    group by team_id, season_year
)

select
    d.league_code,
    d.team_id,
    d.season_year,
    d.player_id,
    d.player_name,
    d.raw_ingested_at,
    d.n_dupes,
    r.n_distinct_ingested_at,
    r.earliest_ingest,
    r.latest_ingest
from dupes d
join raw_payload_counts r using (team_id, season_year)
order by d.team_id, d.season_year, d.player_id, d.raw_ingested_at
limit 100
