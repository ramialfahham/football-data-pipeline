{{ config(materialized='table') }}

{#
  W1 last-5 momentum builder — team.

  For each upcoming fixture side, finds the team's last 5 finished matches
  (cross-competition, same entity_type, same season_api_year, kickoff before
  this fixture) and aggregates raw totals. No ratios — those are computed in
  mart_momentum__team.

  Grain: (upcoming_fixture_sk, team_sk).

  Scope: all competition types — club and national. W1 (last 5) is shown
  alongside W2 for every fixture; both numbers are always presented together.

  Season boundary:
  - Club: season_api_year = upcoming fixture's season (real calendar boundary).
  - National: no season_api_year cap — qualifying campaigns and tournament
    cycles span multiple API seasons; recency alone is the correct boundary.

  Returns no row when a team has no finished matches yet (before phase for a
  club domestic_league). The mart will emit nulls; #326 fills the gap.

  Player-derived columns (key_passes, tackles, …) inherit player-stat coverage
  gaps: if none of the 5 legs have player data the column is NULL; if some do,
  the sum covers only those matches. games_with_player_stats tracks coverage.

  Coverage rule (same-window): a ratio's numerator and denominator must cover the
  same games. Team stats (shots, passes, corners, saves) are sparse in lower
  leagues, so the builder carries per-input coverage counts and coverage-restricted
  scoreline sums; the mart divides each metric over the matching window. Where no
  covered game exists the mart yields NULL (we never divide a full-window numerator
  by a partial-window denominator).
#}

with upcoming as (
    select
        fixture_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

registry as (
    select * from {{ ref('competition_registry') }}
),

types as (
    select * from {{ ref('competition_types') }}
),

upcoming_with_type as (
    select
        u.fixture_sk,
        u.home_team_sk,
        u.away_team_sk,
        u.league_code,
        u.season_api_year,
        u.kickoff_datetime,
        reg.competition_type,
        typ.entity_type
    from upcoming as u
    left join registry as reg
        on u.league_code = reg.league_code
    left join types as typ
        on reg.competition_type = typ.competition_type
),

-- Expand each fixture into two sides (home + away)
upcoming_sides as (
    select
        fixture_sk as upcoming_fixture_sk,
        home_team_sk as team_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        entity_type
    from upcoming_with_type

    union all

    select
        fixture_sk as upcoming_fixture_sk,
        away_team_sk as team_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        entity_type
    from upcoming_with_type
),

-- For each side, rank the team's recent legs (same entity_type + season, before kickoff)
ranked_legs as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        s.season_api_year,
        s.entity_type,
        l.fixture_sk as leg_fixture_sk,
        l.league_code as leg_league_code,
        l.result,
        l.goals_for,
        l.goals_against,
        l.shots_total,
        l.shots_on_goal,
        l.shots_inside_box,
        l.passes_total,
        l.passes_accurate,
        l.corner_kicks,
        l.opponent_corner_kicks,
        l.goalkeeper_saves,
        l.opponent_shots_on_goal,
        row_number() over (
            partition by s.upcoming_fixture_sk, s.team_sk
            order by l.kickoff_datetime desc
        ) as recency_rank
    from upcoming_sides as s
    inner join {{ ref('int_legs__team_match') }} as l
        on
            s.team_sk = l.team_sk
            and s.entity_type = l.entity_type
            and s.kickoff_datetime > l.kickoff_datetime
            -- Club: restrict to current season (seasons are real calendar boundaries).
            -- National: no season cap — a WC campaign spans multiple season_api_years
            -- (qualifiers 2024/25 + tournament 2026); recency alone is the boundary.
            and (
                s.entity_type = 'national'
                or s.season_api_year = l.season_api_year
            )
),

last_5 as (
    select *
    from ranked_legs
    where recency_rank <= 5
),

-- Aggregate raw totals over the last 5 team-match legs
team_agg as (
    select
        upcoming_fixture_sk,
        team_sk,
        season_api_year,
        entity_type,
        count(*) as games_in_window,
        -- per-input coverage: stats are sparse in lower leagues, so each rate
        -- must divide over the games where its inputs actually exist
        countif(shots_total is not null) as games_with_team_stats,
        countif(opponent_corner_kicks is not null) as games_with_opp_stats,
        array_agg(distinct leg_league_code order by leg_league_code)
            as contributing_competitions,
        sum(case result when 'W' then 3 when 'D' then 1 else 0 end)
            as points_won,
        sum(goals_for) as goals_for,
        sum(goals_against) as goals_against,
        -- coverage-restricted scoreline sums keep finishing_efficiency and
        -- save_ratio same-window with their stat denominators
        sum(if(shots_on_goal is not null, goals_for, null))
            as goals_for_in_shot_games,
        sum(if(goalkeeper_saves is not null, goals_against, null))
            as goals_against_in_save_games,
        sum(shots_total) as shots_total,
        sum(shots_on_goal) as shots_on_goal,
        sum(shots_inside_box) as shots_inside_box,
        sum(passes_total) as passes_total,
        sum(passes_accurate) as passes_accurate,
        sum(corner_kicks) as corner_kicks,
        sum(opponent_corner_kicks) as opponent_corner_kicks,
        sum(goalkeeper_saves) as goalkeeper_saves
    from last_5
    group by
        upcoming_fixture_sk,
        team_sk,
        season_api_year,
        entity_type
),

-- Sum player-derived stats for the same 5 legs (inherits player-stat coverage gaps)
player_derived as (
    select
        l5.upcoming_fixture_sk,
        l5.team_sk,
        countif(p.fixture_sk is not null) as games_with_player_stats,
        sum(p.key_passes) as key_passes,
        sum(p.tackles) as tackles,
        sum(p.interceptions) as interceptions,
        sum(p.blocks) as blocks,
        sum(p.duels_total) as duels_total,
        sum(p.duels_won) as duels_won,
        sum(p.dribbles_attempts) as dribbles_attempts,
        sum(p.dribbles_success) as dribbles_success
    from last_5 as l5
    left join {{ ref('int_legs__team_from_players') }} as p
        on
            l5.leg_fixture_sk = p.fixture_sk
            and l5.team_sk = p.team_sk
    group by
        l5.upcoming_fixture_sk,
        l5.team_sk
)

select
    ta.upcoming_fixture_sk,
    ta.team_sk,
    ta.season_api_year,
    ta.entity_type,
    'last_5' as window_type,
    ta.games_in_window,
    ta.games_with_team_stats,
    ta.games_with_opp_stats,
    ta.contributing_competitions,
    ta.points_won,
    ta.goals_for,
    ta.goals_against,
    ta.goals_for_in_shot_games,
    ta.goals_against_in_save_games,
    ta.shots_total,
    ta.shots_on_goal,
    ta.shots_inside_box,
    ta.passes_total,
    ta.passes_accurate,
    ta.corner_kicks,
    ta.opponent_corner_kicks,
    ta.goalkeeper_saves,
    pd.games_with_player_stats,
    pd.key_passes,
    pd.tackles,
    pd.interceptions,
    pd.blocks,
    pd.duels_total,
    pd.duels_won,
    pd.dribbles_attempts,
    pd.dribbles_success
from team_agg as ta
left join player_derived as pd
    on
        ta.upcoming_fixture_sk = pd.upcoming_fixture_sk
        and ta.team_sk = pd.team_sk
