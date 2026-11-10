-- A club in a continental club competition belongs to that competition's confederation. One row
-- per club and competition that breaks it. It catches a fixture filed under a same-named club from
-- another continent. Checked only where both confederations are stored, so a club with no country
-- or a country with no confederation is left to the tests that own those.

{{ config(store_failures = true, severity = 'error') }}

with fixtures as (
    select
        fixture_api_id,
        league_code,
        home_team_api_id as team_api_id
    from {{ ref('fct_fixture') }}
    union all
    select
        fixture_api_id,
        league_code,
        away_team_api_id as team_api_id
    from {{ ref('fct_fixture') }}
),

club_competitions as (
    select
        league_code,
        confederation
    from {{ ref('dim_league') }}
    where competition_type in ('continental_cup', 'club_qualifying', 'continental_super_cup')
),

clubs as (
    select
        dim_team.team_api_id,
        dim_team.team_name,
        dim_team.team_country,
        dim_country.confederation
    from {{ ref('dim_team') }} as dim_team
    inner join {{ ref('dim_country') }} as dim_country
        on dim_team.team_country = dim_country.country_name
    where not coalesce(dim_team.is_national_team, false)
)

select
    fixtures.league_code,
    club_competitions.confederation as competition_confederation,
    clubs.team_api_id,
    clubs.team_name,
    clubs.team_country,
    clubs.confederation as team_confederation,
    count(*) as fixtures,
    string_agg(cast(fixtures.fixture_api_id as string), ', ' order by fixtures.fixture_api_id)
        as fixture_ids
from fixtures
inner join club_competitions
    on fixtures.league_code = club_competitions.league_code
inner join clubs
    on fixtures.team_api_id = clubs.team_api_id
where clubs.confederation != club_competitions.confederation
group by 1, 2, 3, 4, 5, 6
