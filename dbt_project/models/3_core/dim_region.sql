{{ config(materialized='table') }}

{#
    The region dimension (#69) — the counterpart to dim_country. A competition points at ONE of the
    two: a domestic competition has a country, a continental or international one has a region.
    Which relationship is populated IS the answer, which is what removes the need for a
    competition_types.single_country flag.

    Published from confederations.csv, which shipped in #57 and has been read by nothing since.

    ⚠ region_key HOLDS A CONFEDERATION CODE — UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC, FIFA. The
    seed keeps `confederation` as its column name because it is the authoring surface and #57
    shipped it that way; the dim publishes it under the name its consumers read, which is a region.
    FIFA -> World is the one row that is a judgement rather than geography, recorded on the seed.

    ⚠ WHAT THIS DOES NOT ADD. competition_registry.confederation ALREADY carries a relationships
    test to ref('confederations') (seeds/schema.yml), so the competition->region guard exists at
    seed level today. This dim buys publication and symmetry with dim_country, not a new guard.
    Saying otherwise would overstate it.

    READ by mart_competition_index.region_label for the competitions with no country — see
    dim_country's note.
#}

with import_confederations as (
    select * from {{ ref('confederations') }}
)

select
    confederation as region_key,
    label_en as region_name,
    label_i18n_key as region_name_i18n_key
from import_confederations
