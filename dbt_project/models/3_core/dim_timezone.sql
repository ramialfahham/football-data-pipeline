{#
    The time zones a country or a venue may name, published from the time_zones seed. A
    relationships test to this dim refuses a misspelt zone. Offsets and daylight-saving dates are
    stored nowhere: BigQuery computes the local time per kick-off date, and only the abbreviation
    it cannot print (CET, CEST) is carried, as label_standard and label_daylight. Grain: time_zone.

    READ by dim_country.time_zone, dim_venue.time_zone and fct_fixture.kickoff_time_zone, each a
    `relationships` test to time_zone.
#}

with import_time_zones as (
    select * from {{ ref('time_zones') }}
)

select
    time_zone,
    label_standard,
    label_daylight
from import_time_zones
