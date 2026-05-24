{{ config(materialized='table') }}

{#
  Player insights mart for upcoming fixtures.
  Grain: (fixture_sk, team_sk, player_sk, leaderboard_id).

  Source: int_matchday__fixture_player_insights — one row per (upcoming fixture, team, player).
  Each player is expanded to 9 leaderboard rows.

  Ranking: within (fixture_sk, team_sk, leaderboard_id), eligible players are ranked by sort_score
  desc, minutes_played_window desc, player_sk asc. Eligible = form_source_unavailable_reason IS NULL
  AND matches_in_window > 0. rank_for_leaderboard is 1–5 for the top-5 eligible; null otherwise.
  Ineligible players (form_source_unavailable_reason set) are included with null rank and null atoms
  so the UI can render "Not provided" copy.

  Leaderboard sort logic (from docs/player_metrics_catalogue.md):
    scorer_points     → goals + assists
    shots_on_target   → shots_on
    dribbles          → dribbles_success
    key_passes        → passes_key
    pass_accuracy     → pass_accuracy_pct (nulls last)
    duels             → duels_won_pct (nulls last)
    defensive_actions → tackles + interceptions + blocks
    save_pct          → save_pct (nulls last)
    cards             → cards_yellow + cards_red

  Tie-break: minutes_played_window desc, player_sk asc.
#}

with import_insights as (
    select * from {{ ref('int_matchday__fixture_player_insights') }}
),

import_dim_player as (
    select player_sk, player_api_id, player_name
    from {{ ref('dim_player') }}
),

import_dim_team as (
    select team_sk, team_api_id
    from {{ ref('dim_team') }}
),

import_fct_fixture as (
    select fixture_sk, fixture_api_id
    from {{ ref('fct_fixture') }}
),

-- Most recently seen position_code per player (informational; not used for filtering)
player_positions as (
    select
        player_sk,
        array_agg(
            position_code ignore nulls
            order by fixture_sk desc
            limit 1
        )[safe_offset(0)] as position_code
    from {{ ref('fct_fixture_player_stats') }}
    group by player_sk
),

-- ─── Expand each player to 9 leaderboard rows ─────────────────────────────

lb_scorer_points as (
    select
        *,
        'scorer_points' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then cast(coalesce(goals, 0) + coalesce(assists, 0) as float64)
        end as sort_score
    from import_insights
),

lb_shots_on_target as (
    select
        *,
        'shots_on_target' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then cast(coalesce(shots_on, 0) as float64)
        end as sort_score
    from import_insights
),

lb_dribbles as (
    select
        *,
        'dribbles' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then cast(coalesce(dribbles_success, 0) as float64)
        end as sort_score
    from import_insights
),

lb_key_passes as (
    select
        *,
        'key_passes' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then cast(coalesce(passes_key, 0) as float64)
        end as sort_score
    from import_insights
),

lb_pass_accuracy as (
    select
        *,
        'pass_accuracy' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then pass_accuracy_pct
        end as sort_score
    from import_insights
),

lb_duels as (
    select
        *,
        'duels' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then duels_won_pct
        end as sort_score
    from import_insights
),

lb_defensive_actions as (
    select
        *,
        'defensive_actions' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then cast(
                    coalesce(tackles_total, 0)
                    + coalesce(interceptions, 0)
                    + coalesce(blocks, 0)
                    as float64
                )
        end as sort_score
    from import_insights
),

lb_save_pct as (
    select
        *,
        'save_pct' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then save_pct
        end as sort_score
    from import_insights
),

lb_cards as (
    select
        *,
        'cards' as leaderboard_id,
        case
            when form_source_unavailable_reason is null and matches_in_window > 0
                then cast(coalesce(cards_yellow, 0) + coalesce(cards_red, 0) as float64)
        end as sort_score
    from import_insights
),

all_leaderboards as (
    select * from lb_scorer_points
    union all
    select * from lb_shots_on_target
    union all
    select * from lb_dribbles
    union all
    select * from lb_key_passes
    union all
    select * from lb_pass_accuracy
    union all
    select * from lb_duels
    union all
    select * from lb_defensive_actions
    union all
    select * from lb_save_pct
    union all
    select * from lb_cards
),

-- ─── Rank within (fixture, team, leaderboard) ─────────────────────────────
-- NULLS LAST means ineligible players (sort_score IS NULL) always rank after eligible ones.
-- rank_for_leaderboard is set only for positions 1–5 when the player has a non-null sort_score.

ranked as (
    select
        *,
        row_number() over (
            partition by fixture_sk, team_sk, leaderboard_id
            order by sort_score desc nulls last, minutes_played_window desc, player_sk asc
        ) as rn
    from all_leaderboards
)

select
    r.fixture_sk,
    f.fixture_api_id,
    r.team_sk,
    dt.team_api_id,
    r.player_sk,
    dp.player_api_id,
    dp.player_name,
    coalesce(pp.position_code, 'UNK') as player_position_code,
    r.league_code,
    r.leaderboard_id,
    case when r.rn <= 5 and r.sort_score is not null then cast(r.rn as int64) end as rank_for_leaderboard,
    r.sort_score,
    r.form_source_league_code,
    r.form_window_kind,
    r.form_source_unavailable_reason,
    r.matches_in_window,
    r.minutes_played_window,
    -- Atoms (null when form_source_unavailable_reason is set — enforced upstream)
    r.goals,
    r.assists,
    r.shots_on,
    r.dribbles_success,
    r.dribbles_attempts,
    r.dribbles_success_pct,
    r.passes_key,
    r.passes_total,
    r.passes_accurate,
    r.pass_accuracy_pct,
    r.duels_total,
    r.duels_won,
    r.duels_won_pct,
    r.tackles_total as tackles,
    r.interceptions,
    r.blocks,
    r.goals_saves,
    r.goals_conceded,
    r.save_pct,
    r.cards_yellow,
    r.cards_red
from ranked as r
inner join import_dim_player as dp on r.player_sk = dp.player_sk
inner join import_dim_team as dt on r.team_sk = dt.team_sk
inner join import_fct_fixture as f on r.fixture_sk = f.fixture_sk
left join player_positions as pp on r.player_sk = pp.player_sk
