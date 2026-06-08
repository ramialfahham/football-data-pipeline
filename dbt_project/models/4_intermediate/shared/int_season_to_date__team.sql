{{ config(materialized='table') }}

{#
  W2 season-to-date builder — team. Cumulative running totals over a team's finished
  matches within one competition+season, one row per match played (the totals THROUGH
  that match). The complement to int_momentum__team (W1 = last 5): this answers
  "what have they done in this competition this season?".

  Grain: (team_sk, league_code, season_api_year, fixture_sk).

  Ordered by kickoff. Carries round_order (the matchday number parsed from round_name)
  and match_number (the team's Nth match that season) so the deferred year-over-year
  surface can align two seasons by matchday without a rewrite.

  Season-bounded: partitioned by (league_code, season_api_year). This covers clubs and
  single-season tournaments (WC/continental — the latest row is "all matches so far in
  the tournament"). Multi-season national qualifier campaigns are a separate follow-up.

  Coverage rule (same as #320): per-match team stats are sparse in some competitions, so
  the builder carries cumulative per-input coverage counts and coverage-restricted
  cumulative scoreline sums; the mart divides each metric over the matching window and
  yields NULL where no covered game exists. Raw sums only — ratios live in the mart.
#}

with team_legs as (
    select * from {{ ref('int_legs__team_match') }}
),

player_legs as (
    select * from {{ ref('int_legs__team_from_players') }}
),

-- One row per (team, finished match) with points + player-derived team stats attached
legs as (
    select
        tl.fixture_sk,
        tl.team_sk,
        tl.league_code,
        tl.season_api_year,
        tl.entity_type,
        tl.kickoff_datetime,
        tl.round_order,
        tl.goals_for,
        tl.goals_against,
        tl.shots_total,
        tl.shots_on_goal,
        tl.shots_inside_box,
        tl.passes_total,
        tl.passes_accurate,
        tl.corner_kicks,
        tl.opponent_corner_kicks,
        tl.goalkeeper_saves,
        case tl.result when 'W' then 3 when 'D' then 1 else 0 end as points,
        pl.fixture_sk is not null as has_player_stats,
        pl.key_passes,
        pl.tackles,
        pl.interceptions,
        pl.blocks,
        pl.duels_total,
        pl.duels_won,
        pl.dribbles_attempts,
        pl.dribbles_success
    from team_legs as tl
    left join player_legs as pl
        on
            tl.fixture_sk = pl.fixture_sk
            and tl.team_sk = pl.team_sk
)

select
    team_sk,
    league_code,
    season_api_year,
    fixture_sk,
    entity_type,
    kickoff_datetime,
    round_order,
    'season_to_date' as window_type,
    row_number() over w_seq as match_number,
    row_number() over w_seq as games_played,
    -- scoreline (always present)
    sum(points) over w as points_won,
    sum(goals_for) over w as goals_for,
    sum(goals_against) over w as goals_against,
    -- team-stat coverage (cumulative)
    sum(case when shots_total is not null then 1 else 0 end) over w
        as games_with_team_stats,
    sum(case when opponent_corner_kicks is not null then 1 else 0 end) over w
        as games_with_opp_stats,
    -- coverage-restricted scoreline sums keep finishing/save same-window
    sum(if(shots_on_goal is not null, goals_for, null)) over w
        as goals_for_in_shot_games,
    sum(if(goalkeeper_saves is not null, goals_against, null)) over w
        as goals_against_in_save_games,
    -- team stats (cumulative)
    sum(shots_total) over w as shots_total,
    sum(shots_on_goal) over w as shots_on_goal,
    sum(shots_inside_box) over w as shots_inside_box,
    sum(passes_total) over w as passes_total,
    sum(passes_accurate) over w as passes_accurate,
    sum(corner_kicks) over w as corner_kicks,
    sum(opponent_corner_kicks) over w as opponent_corner_kicks,
    sum(goalkeeper_saves) over w as goalkeeper_saves,
    -- player-derived team stats (cumulative; inherit player-stat coverage gaps)
    sum(case when has_player_stats then 1 else 0 end) over w
        as games_with_player_stats,
    sum(key_passes) over w as key_passes,
    sum(tackles) over w as tackles,
    sum(interceptions) over w as interceptions,
    sum(blocks) over w as blocks,
    sum(duels_total) over w as duels_total,
    sum(duels_won) over w as duels_won,
    sum(dribbles_attempts) over w as dribbles_attempts,
    sum(dribbles_success) over w as dribbles_success
from legs
window
    w as (
        partition by team_sk, league_code, season_api_year
        order by kickoff_datetime asc, fixture_sk asc
        rows between unbounded preceding and current row
    ),
    w_seq as (
        partition by team_sk, league_code, season_api_year
        order by kickoff_datetime asc, fixture_sk asc
    )
