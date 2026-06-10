{{ config(materialized='table') }}

{#
  W1 last-5 form-window selection — team.

  For each upcoming fixture side, selects the team's last 5 finished matches
  (cross-competition, same entity_type, kickoff before this fixture) and keeps
  them UN-aggregated — one row per window leg, with the leg's stats and
  descriptors. Extracted from int_momentum__team (#323) so the aggregate
  (momentum) and its drill-down list (mart_form_window__team) consume the same
  selection and cannot drift.

  Grain: (upcoming_fixture_sk, team_sk, leg_fixture_sk).

  Season boundary (unchanged from #320):
  - Club: season_api_year = upcoming fixture's season (real calendar boundary).
  - National: no season_api_year cap — qualifying campaigns and tournament
    cycles span multiple API seasons; recency alone is the correct boundary.

  Returns no rows when a team has no finished matches yet (before phase for a
  club domestic_league); #326's season-to-date fallback covers that gap.
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
        l.kickoff_datetime as leg_kickoff_datetime,
        l.round_name as leg_round_name,
        l.home_away,
        l.opponent_team_sk,
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
)

select *
from ranked_legs
where recency_rank <= 5
