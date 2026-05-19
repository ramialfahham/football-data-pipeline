-- Unified per-team fixture statistics across all onboarded competitions (explicit ref() list).
-- Deduplicated to latest ingest per (league_code, fixture_id, team_id).
-- Output grain: (league_code, fixture_id, team_id).

-- When adding a competition: add `import_stg_<code>_fixture_statistics` below and the same name here.
{% set fixture_statistics_union_ctes = [
    'import_stg_bl1_fixture_statistics',
    'import_stg_wc_fixture_statistics',
    'import_stg_wcqeu_fixture_statistics',
    'import_stg_wcqaf_fixture_statistics',
    'import_stg_wcqca_fixture_statistics',
    'import_stg_wcqsa_fixture_statistics',
    'import_stg_wcqas_fixture_statistics',
    'import_stg_wcqip_fixture_statistics',
    'import_stg_wcqoc_fixture_statistics',
    'import_stg_pl_fixture_statistics',
    'import_stg_pd_fixture_statistics',
    'import_stg_bl2_fixture_statistics',
    'import_stg_l1_fixture_statistics',
    'import_stg_vl_fixture_statistics',
    'import_stg_sa_fixture_statistics',
] %}

with import_stg_bl1_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__bl1_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wc_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wc_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wcqeu_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wcqeu_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wcqaf_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wcqaf_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wcqca_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wcqca_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wcqsa_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wcqsa_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wcqas_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wcqas_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wcqip_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wcqip_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_wcqoc_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__wcqoc_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_pl_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__pl_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_pd_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__pd_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_bl2_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__bl2_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_sa_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__sa_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_l1_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__l1_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

import_stg_vl_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__vl_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

unioned_fixture_statistics as (
    {{ union_all(fixture_statistics_union_ctes) }}
),

deduped_fixture_statistics as (
    select *
    from unioned_fixture_statistics
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    fixture_id,
    team_id,
    shots_on_goal,
    shots_off_goal,
    shots_total,
    shots_blocked,
    shots_inside_box,
    shots_outside_box,
    fouls,
    corner_kicks,
    offsides,
    ball_possession_percent,
    yellow_cards,
    red_cards,
    goalkeeper_saves,
    passes_total,
    passes_accurate,
    passes_accuracy_percent,
    raw_ingested_at
from deduped_fixture_statistics
