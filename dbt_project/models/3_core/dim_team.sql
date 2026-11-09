with import_base_apif__teams_global as (
    select * from {{ ref('base_apif__teams_global') }}
),

import_base_apif__fixtures_next as (
    select * from {{ ref('base_apif__fixtures_next') }}
),

import_dim_league as (
    select * from {{ ref('dim_league') }}
),

fixture_sides as (
    select
        league_code,
        home_team_id as team_api_id
    from import_base_apif__fixtures_next
    union distinct
    select
        league_code,
        away_team_id as team_api_id
    from import_base_apif__fixtures_next
),

-- a national team is a team with a fixture in a national-team competition; the provider's /teams
-- list for such a competition can also hold a club, so the fixtures decide
national_teams as (
    select distinct fixture_sides.team_api_id
    from fixture_sides
    inner join import_dim_league as leagues
        on fixture_sides.league_code = leagues.league_code
    where leagues.entity_type = 'national'
)

-- team_slug is the team's permanent, locale-independent URL segment
-- (/{locale}/teams/{team_slug}/, docs/site_architecture.md section 3). Derived in base and
-- merely published here, like every other attribute: base prepares, the dim propagates.
-- It carries no provider id except in the terminal collision case.
select
    cast(teams.team_api_id as int64) as team_sk,
    teams.team_api_id,
    teams.team_name,
    teams.team_slug,
    teams.team_code,
    teams.team_country,
    teams.team_founded_year,
    teams.team_logo_url,
    teams.venue_api_id,
    teams.venue_name,
    teams.venue_address,
    teams.venue_city,
    teams.venue_capacity,
    teams.raw_ingested_at,
    national_teams.team_api_id is not null as is_national_team
from import_base_apif__teams_global as teams
left join national_teams
    on teams.team_api_id = national_teams.team_api_id
