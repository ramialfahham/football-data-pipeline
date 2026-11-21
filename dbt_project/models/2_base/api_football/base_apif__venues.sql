-- One row per provider venue that a fixture names, with the country it lies in.
-- Entity resolution for dim_venue: the fixtures give a venue id, name and city but no country,
-- and the country comes from the other sources, in this order: the country of the competitions
-- its fixtures belong to, the country of a team whose home ground the venue is, the country most
-- of its home teams belong to. Grain: venue_api_id.

with import_fixtures as (
    select * from {{ ref('base_apif__fixtures_next') }}
),

import_teams as (
    select * from {{ ref('base_apif__teams_global') }}
),

import_leagues as (
    select * from {{ ref('base_apif__league_entity') }}
),

fixture_venues as (
    select
        venue_id as venue_api_id,
        venue_name,
        venue_city,
        league_code,
        cast(home_team_id as int64) as home_team_id,
        raw_ingested_at
    from import_fixtures
    where venue_id is not null
),

latest_label as (
    select
        venue_api_id,
        venue_name,
        venue_city
    from fixture_venues
    qualify row_number() over (
        partition by venue_api_id
        order by raw_ingested_at desc, venue_name asc, venue_city asc
    ) = 1
),

competition_country as (
    select
        fixture_venues.venue_api_id,
        import_leagues.league_country as country_name
    from fixture_venues
    inner join import_leagues
        on fixture_venues.league_code = import_leagues.league_code
    where import_leagues.league_country is not null
    group by fixture_venues.venue_api_id, import_leagues.league_country
    qualify row_number() over (
        partition by fixture_venues.venue_api_id
        order by count(*) desc, import_leagues.league_country asc
    ) = 1
),

ground_country as (
    select
        venue_api_id,
        min(team_country) as country_name
    from import_teams
    where venue_api_id is not null and team_country is not null
    group by venue_api_id
),

home_team_country as (
    select
        fixture_venues.venue_api_id,
        import_teams.team_country as country_name
    from fixture_venues
    inner join import_teams
        on fixture_venues.home_team_id = cast(import_teams.team_api_id as int64)
    where import_teams.team_country is not null
    group by fixture_venues.venue_api_id, import_teams.team_country
    qualify row_number() over (
        partition by fixture_venues.venue_api_id
        order by count(*) desc, import_teams.team_country asc
    ) = 1
)

select
    latest_label.venue_api_id,
    latest_label.venue_name,
    latest_label.venue_city,
    coalesce(
        competition_country.country_name,
        ground_country.country_name,
        home_team_country.country_name
    ) as country_name
from latest_label
left join competition_country
    on latest_label.venue_api_id = competition_country.venue_api_id
left join ground_country
    on latest_label.venue_api_id = ground_country.venue_api_id
left join home_team_country
    on latest_label.venue_api_id = home_team_country.venue_api_id
