{{ config(materialized='table') }}

{#
  W1 last-5 momentum builder — player.

  For each upcoming fixture side, identifies the team's last 5 finished matches
  (same entity_type, same season_api_year, before this fixture's kickoff) and
  aggregates raw player stat totals for every player who appeared in those matches.
  No ratios — those are computed in mart_momentum__player.

  Grain: (upcoming_fixture_sk, team_sk, player_sk).

  Scope: all competition types — club and national. W1 (last 5) is shown
  alongside W2 for every fixture; both numbers are always presented together.

  Season boundary:
  - Club: season_api_year = upcoming fixture's season (real calendar boundary).
  - National: no season_api_year cap — qualifying campaigns and tournament
    cycles span multiple API seasons; recency alone is the correct boundary.

  A player absent from some of the 5 matches contributes stats only for the
  matches they appeared in — honest absence, not zero. games_in_window reflects
  the team window (max 5), not the player's individual appearance count.

  passes_accurate is derived per fixture as ROUND(passes_total *
  passes_accuracy_percent / 100) then summed; inherits small rounding error.

  save_pct requires goals_conceded which is not currently carried in
  int_legs__player_match — mart_momentum__player will emit null for that metric.
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

-- Identify the team's last 5 match fixture_sks (mirrors int_momentum__team logic)
ranked_team_legs as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        s.season_api_year,
        s.entity_type,
        l.fixture_sk as leg_fixture_sk,
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

last_5_fixtures as (
    select
        upcoming_fixture_sk,
        team_sk,
        season_api_year,
        entity_type,
        leg_fixture_sk
    from ranked_team_legs
    where recency_rank <= 5
),

-- Aggregate player stats across the team's last 5 matches
player_agg as (
    select
        lf.upcoming_fixture_sk,
        lf.team_sk,
        p.player_sk,
        lf.season_api_year,
        lf.entity_type,
        count(*) as games_in_window,
        any_value(p.position_code) as position_code,
        sum(p.goals_total) as goals_total,
        sum(p.goals_conceded) as goals_conceded,
        sum(p.goals_assists) as goals_assists,
        sum(p.goals_saves) as goals_saves,
        sum(p.shots_total) as shots_total,
        sum(p.shots_on) as shots_on,
        sum(p.passes_total) as passes_total,
        sum(p.passes_key) as passes_key,
        sum(p.tackles_total) as tackles_total,
        sum(p.tackles_blocks) as tackles_blocks,
        sum(p.tackles_interceptions) as tackles_interceptions,
        sum(p.duels_total) as duels_total,
        sum(p.duels_won) as duels_won,
        sum(p.dribbles_attempts) as dribbles_attempts,
        sum(p.dribbles_success) as dribbles_success,
        sum(p.cards_yellow) as cards_yellow,
        sum(p.cards_red) as cards_red,
        sum(p.offsides) as offsides,
        sum(p.dribbles_past) as dribbles_past,
        sum(p.penalty_won) as penalty_won,
        sum(p.penalty_committed) as penalty_committed,
        -- passes_accurate: derived per fixture, then summed (small rounding error)
        sum(
            safe_cast(
                round(p.passes_total * p.passes_accuracy_percent / 100.0) as int64
            )
        ) as passes_accurate
    from last_5_fixtures as lf
    inner join {{ ref('int_legs__player_match') }} as p
        on
            lf.leg_fixture_sk = p.fixture_sk
            and lf.team_sk = p.team_sk
    group by
        lf.upcoming_fixture_sk,
        lf.team_sk,
        p.player_sk,
        lf.season_api_year,
        lf.entity_type
)

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    season_api_year,
    entity_type,
    'last_5' as window_type,
    games_in_window,
    position_code,
    goals_total,
    goals_conceded,
    goals_assists,
    goals_saves,
    shots_total,
    shots_on,
    passes_total,
    passes_key,
    passes_accurate,
    tackles_total,
    tackles_blocks,
    tackles_interceptions,
    duels_total,
    duels_won,
    dribbles_attempts,
    dribbles_success,
    cards_yellow,
    cards_red,
    offsides,
    dribbles_past,
    penalty_won,
    penalty_committed
from player_agg
