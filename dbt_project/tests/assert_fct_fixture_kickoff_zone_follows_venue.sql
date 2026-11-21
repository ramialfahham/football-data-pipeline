{#
  A fixture's zone is its venue's, else its competition country's, else UTC; its local kick-off is
  its UTC kick-off on that zone's clock; a fixture with no zone is labelled UTC. Returns the
  fixtures that break any of the three.
#}

with fixtures as (
    select
        fixture_sk,
        venue_api_id,
        league_code,
        kickoff_datetime,
        kickoff_time_zone,
        kickoff_local,
        kickoff_zone_label
    from {{ ref('fct_fixture') }}
),

expected as (
    select
        fixtures.*,
        coalesce(venues.time_zone, countries.time_zone) as served_zone
    from fixtures
    left join {{ ref('dim_venue') }} as venues
        on fixtures.venue_api_id = venues.venue_api_id
    left join {{ ref('dim_league') }} as leagues
        on fixtures.league_code = leagues.league_code
    left join {{ ref('dim_country') }} as countries
        on leagues.league_country = countries.country_name
)

select *
from expected
where
    kickoff_time_zone != coalesce(served_zone, 'UTC')
    or kickoff_local != datetime(kickoff_datetime, kickoff_time_zone)
    or (served_zone is null and kickoff_zone_label != 'UTC')
