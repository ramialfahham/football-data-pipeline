{{ config(materialized='table') }}

{#
    Per-player, per-season rollup (the lighter season surface; feeds mart_top_scorers).

    #480 consolidation: now COMPOSES the shared int_player_season__metrics instead of
    re-aggregating fct_fixture_player_stats inline. Pass accuracy is now the catalogue-correct
    WEIGHTED value (`pass_accuracy_pct` = accurate ÷ attempted) — the previous
    `pass_accuracy_avg_percent` was a naive average of per-fixture percentages (wrong for low-volume
    games) and was unconsumed; corrected here as part of the consolidation. rating_avg preserved.

    A player who moves clubs mid-season produces one row per competition-season (today's grain; the
    per-club split is the deferred §8.3 follow-up). Grain: (player_sk, season_sk).
#}

with season as (
    select * from {{ ref('int_player_season__metrics') }}
),

dim_player as (
    select * from {{ ref('dim_player') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['s.player_sk', 's.season_sk']) }} as player_season_sk,
    s.player_sk,
    s.season_sk,
    s.league_sk,
    s.league_code,
    s.season_api_year,
    p.player_name,
    p.player_first_name,
    p.player_last_name,
    p.player_nationality,
    p.player_birth_date,
    s.appearances,
    s.starts,
    s.substitute_appearances,
    s.minutes,
    s.goals,
    s.assists,
    s.shots_total as shots,
    s.shots_on_target,
    s.passes_key as key_passes,
    s.rating_avg,
    s.pass_accuracy_pct,
    s.cards_yellow as yellow_cards,
    s.cards_red as red_cards
from season as s
left join dim_player as p on s.player_sk = p.player_sk
