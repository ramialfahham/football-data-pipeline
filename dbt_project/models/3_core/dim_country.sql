{{ config(materialized='table') }}

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

    ⚠ NOT "UN countries". 188 of the 224 rows are UN states; the rest are football associations
    (England n=2723, Scotland, Wales, Northern Ireland, Kosovo, Chinese Taipei), territories that
    produce players, one unrecognised state and one historical (Yugoslavia, for players born
    before 1992). Dropping any of them is not an option — England is the single most common value
    in the whole dataset. #69's discovery note carries the breakdown.

    ⚠ NOTHING READS THIS YET. The foreign keys from the four free-text columns are #69 step 5 and
    a separate MR; mart_competition_index is #62 step 3. Additive and not yet read, the same
    pattern confederations.csv shipped under in #57.
#}

with import_countries as (
    select * from {{ ref('countries') }}
)

select
    country_key,
    country_name
from import_countries
