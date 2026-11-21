{#
    The canonical country dimension (#69). Countries existed nowhere in the model layer before
    this: they were free text in four dims (dim_league, dim_team, dim_player, dim_coach), spelled
    up to three ways for the same country, with no list of what "valid" looked like.

    Published from the countries seed, which is the authoring surface. The provider's own spellings
    are mapped onto these names by country_name_overrides, applied in base — this dim publishes,
    it does not correct (feedback_entity_corrections_in_base).

    NO SURROGATE KEY. Every other core dim casts a provider integer id into a _sk; a country has
    no provider id, so country_key IS the key. Inventing a synthetic integer would add a join
    without adding identity.

    ⚠ NOT "UN countries". 189 of the 229 rows are UN states; the rest are football associations
    (England n=2723, Scotland, Wales, Northern Ireland, Kosovo, Chinese Taipei), territories that
    produce players, one unrecognised state and one historical (Yugoslavia, for players born
    before 1992). Dropping any of them is not an option — England is the single most common value
    in the whole dataset. #69's discovery note carries the breakdown.

    READ by dim_league.league_country, dim_team.team_country, dim_player.player_birth_country,
    dim_player.player_nationality and dim_coach.coach_birth_country, each a `relationships` test to
    country_name (#69 step 5); and by
    mart_competition_index.region_label, which relationship (this dim, or dim_region) is populated
    for a competition IS the answer to whether its sub-line shows a country or a region (#62 step 3).
    mart_team_index reads confederation: a team's region is its country's confederation.

    time_zone is the country's default IANA zone from the country_time_zones seed, empty for a
    country whose venues sit in several zones: dim_venue then takes each venue's zone from
    venue_time_zones.
#}

with import_countries as (
    select * from {{ ref('countries') }}
),

import_country_time_zones as (
    select * from {{ ref('country_time_zones') }}
)

select
    import_countries.country_key,
    import_countries.country_name,
    import_countries.confederation,
    import_country_time_zones.time_zone
from import_countries
left join import_country_time_zones
    on import_countries.country_key = import_country_time_zones.country_key
