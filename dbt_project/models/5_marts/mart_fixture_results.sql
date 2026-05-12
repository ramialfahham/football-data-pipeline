{{ config(materialized='view') }}

{#
    Flat fixture table: one row per fixture with both teams, league, season,
    and kickoff-date denormalised. Logic lives in int_matchday__fixture_denormalized;
    this mart keeps the stable consumer name.
#}

select * from {{ ref('int_matchday__fixture_denormalized') }}
