-- Unified standings across all onboarded competitions (explicit ref() list).
-- Deduplicated to latest ingest per (league_code, season, team_id).
-- Output grain: (league_code, season, team_id).

-- When adding a competition: add `import_stg_<code>_standings` below and the same name here.
{% set standings_union_ctes = [
    'import_stg_bl1_standings',
    'import_stg_wc_standings',
    'import_stg_wcqeu_standings',
    'import_stg_wcqaf_standings',
    'import_stg_wcqca_standings',
    'import_stg_wcqsa_standings',
    'import_stg_wcqas_standings',
    'import_stg_wcqip_standings',
    'import_stg_wcqoc_standings',
] %}

with import_stg_bl1_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__bl1_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wc_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wc_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wcqeu_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wcqeu_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wcqaf_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wcqaf_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wcqca_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wcqca_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wcqsa_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wcqsa_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wcqas_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wcqas_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wcqip_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wcqip_standings') }}
    where
        team_id is not null
        and season is not null
),

import_stg_wcqoc_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__wcqoc_standings') }}
    where
        team_id is not null
        and season is not null
),

unioned_standings as (
    {{ union_all(standings_union_ctes) }}
),

deduped_standings as (
    select *
    from unioned_standings
    qualify row_number() over (
        partition by league_code, season, team_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    league_api_id,
    league_name,
    season,
    team_id,
    team_name,
    standing_rank,
    points,
    goals_diff,
    form,
    group_description,
    played_all,
    wins_all,
    draws_all,
    losses_all,
    raw_ingested_at
from deduped_standings
