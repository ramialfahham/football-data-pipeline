{#
    One row per provider venue that a fixture names, with the IANA time zone its kick-offs are
    played in. Grain: venue_api_id.

    The country is resolved in base_apif__venues. The zone is the venue's row in the
    venue_time_zones seed, else its country's default in dim_country. A country that spans zones
    has no default, so a venue of such a country without a seed row has no zone and fails the
    not_null test: a wrong zone is never guessed.
#}

with import_venues as (
    select * from {{ ref('base_apif__venues') }}
),

import_dim_country as (
    select * from {{ ref('dim_country') }}
),

import_venue_time_zones as (
    select * from {{ ref('venue_time_zones') }}
)

select
    cast(import_venues.venue_api_id as int64) as venue_sk,
    import_venues.venue_api_id,
    import_venues.venue_name,
    import_venues.venue_city,
    import_venues.country_name as venue_country,
    coalesce(import_venue_time_zones.time_zone, import_dim_country.time_zone) as time_zone
from import_venues
left join import_venue_time_zones
    on import_venues.venue_api_id = import_venue_time_zones.venue_api_id
left join import_dim_country
    on import_venues.country_name = import_dim_country.country_name
