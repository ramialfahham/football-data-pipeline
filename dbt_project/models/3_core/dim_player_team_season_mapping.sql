{{ config(materialized='table') }}

{#
    Rostered player↔team↔season membership (conformed). One row per player per team
    per season they were in the /players roster — including squad members with zero
    appearances. A relationship (mapping) dimension, not an entity dim and not a fact:
    no measures, no descriptive attributes — only the participating keys (plus lineage).
    Its grain is one row per association occurrence, so joining on a single participating
    key (e.g. player_sk) resolves a many-to-many and returns many rows by design. See the
    "relationship (mapping) dimensions" clause in dbt_project/docs/layering.md.

    Use this to answer "which team/competition was a player part of, when". "Did they
    play" lives in fct_fixture_player_stats; "did they move" lives in fct_transfer.

    A player legitimately produces multiple rows: a mid-season transfer (two teams,
    same season) and club + national-team membership in the same window are both real.

    season_sk / league_sk are resolved by lookup against dim_competition_season on
    (league_code, season_api_year) — the roster source carries league_code, not
    league_api_id. season_sk is nullable: a roster season with no competition-season
    row (uncovered by /leagues) yields null rather than dropping the membership.

    The lookup CTE is reduced to one row per (league_code, season_api_year) first:
    dim_competition_season's TESTED grain is (league_api_id, season_api_year), and a
    league_code maps to one league_api_id by registry design (one provider_league_id
    per competition) — but that 1:1 is not tested, so the dedup guarantees the join
    cannot fan out and duplicate membership rows even if the invariant were violated.
    With the invariant intact it is a no-op.
#}

with base_apif__player_team_season as (
    select * from {{ ref('base_apif__player_team_season') }}
),

dim_competition_season as (
    select
        league_code,
        season_api_year,
        season_sk,
        league_sk
    from {{ ref('dim_competition_season') }}
    qualify row_number() over (
        partition by league_code, season_api_year
        order by season_sk
    ) = 1
)

select
    {{ dbt_utils.generate_surrogate_key([
        'pts.player_id',
        'pts.team_id',
        'pts.league_code',
        'pts.season_year'
    ]) }} as player_team_season_sk,
    cast(pts.player_id as int64) as player_sk,
    cast(pts.team_id as int64) as team_sk,
    cs.season_sk,
    cs.league_sk,
    pts.league_code,
    pts.season_year as season_api_year,
    pts.raw_ingested_at
from base_apif__player_team_season as pts
left join dim_competition_season as cs
    on
        pts.league_code = cs.league_code
        and pts.season_year = cs.season_api_year
