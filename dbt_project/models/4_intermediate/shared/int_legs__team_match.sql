{{ config(materialized='table') }}

{#
  Building-block team-match leg: one row per (team, finished match), carrying that team's
  raw stats AND the opponent's (so danger-zone-conceded etc. are derivable), plus the
  competition's type/entity classification and the dimensions windows need.

  Cross-competition and cross-type — the shared foundation every team performance metric
  aggregates over (a metric = a filter + aggregate of these rows). Grain: (fixture_sk, team_sk).

  Built alongside the legacy int_matchday__finished_fixture_team_leg during migration
  (see issue #321); that one is retired once marts cut over to this.
#}

with fixtures as (
    select * from {{ ref('fct_fixture') }}
),

team_stats as (
    select * from {{ ref('fct_fixture_team_stats') }}
),

registry as (
    select * from {{ ref('competition_registry') }}
),

types as (
    select * from {{ ref('competition_types') }}
),

-- Penalty + own-goal counts per (fixture, team) from match events, for the open-play goal split
-- (CPO Option A, 2026-06-24). event_detail: 'Penalty' = a scored penalty by this team; 'Own Goal'
-- = an own goal THIS team scored into its own net — which counts for the OPPONENT, so it is joined
-- as the opponent's own goals downstream. The remaining goals ('Normal Goal') are open play. Only
-- the components are event-derived; goals_for stays the authoritative scoreline.
events as (
    select
        fixture_sk,
        team_sk,
        countif(event_type = 'Goal' and event_detail = 'Penalty') as penalty_goals,
        countif(event_type = 'Goal' and event_detail = 'Own Goal') as own_goals_scored
    from {{ ref('fct_fixture_event') }}
    where team_sk is not null
    group by fixture_sk, team_sk
),

-- Each finished match as two team legs: the home side's perspective and the away side's.
legs as (
    select
        f.fixture_sk,
        f.league_sk,
        f.season_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.round_name,
        safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
        'home' as home_away,
        f.home_team_sk as team_sk,
        f.away_team_sk as opponent_team_sk,
        f.goals_home as goals_for,
        f.goals_away as goals_against,
        case
            when f.goals_home > f.goals_away then 'W'
            when f.goals_home < f.goals_away then 'L'
            else 'D'
        end as result
    from fixtures as f
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and f.goals_home is not null
        and f.goals_away is not null
    union all
    select
        f.fixture_sk,
        f.league_sk,
        f.season_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.round_name,
        safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
        'away' as home_away,
        f.away_team_sk as team_sk,
        f.home_team_sk as opponent_team_sk,
        f.goals_away as goals_for,
        f.goals_home as goals_against,
        case
            when f.goals_away > f.goals_home then 'W'
            when f.goals_away < f.goals_home then 'L'
            else 'D'
        end as result
    from fixtures as f
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and f.goals_home is not null
        and f.goals_away is not null
),

with_stats as (
    select
        l.fixture_sk,
        l.league_sk,
        l.season_sk,
        l.league_code,
        l.season_api_year,
        l.kickoff_datetime,
        l.round_name,
        l.round_order,
        l.home_away,
        l.team_sk,
        l.opponent_team_sk,
        l.goals_for,
        l.goals_against,
        l.result,
        own.shots_on_goal,
        own.shots_total,
        own.shots_inside_box,
        own.corner_kicks,
        own.passes_total,
        own.passes_accurate,
        own.goalkeeper_saves,
        opp.shots_on_goal as opponent_shots_on_goal,
        opp.shots_total as opponent_shots_total,
        opp.shots_inside_box as opponent_shots_inside_box,
        opp.corner_kicks as opponent_corner_kicks,
        -- open-play goal split (CPO Option A): goals_for stays the authoritative scoreline; this
        -- team's penalties and the own goals credited to it (the OPPONENT's own-goal events) are
        -- subtracted downstream to get goals_open_play. Catalogued as goals_penalty / goals_own.
        coalesce(ev_own.penalty_goals, 0) as goals_penalty,
        coalesce(ev_opp.own_goals_scored, 0) as goals_own
    from legs as l
    left join team_stats as own
        on l.fixture_sk = own.fixture_sk and l.team_sk = own.team_sk
    left join team_stats as opp
        on l.fixture_sk = opp.fixture_sk and l.opponent_team_sk = opp.team_sk
    left join events as ev_own
        on l.fixture_sk = ev_own.fixture_sk and l.team_sk = ev_own.team_sk
    left join events as ev_opp
        on l.fixture_sk = ev_opp.fixture_sk and l.opponent_team_sk = ev_opp.team_sk
)

select
    ws.*,
    reg.competition_type,
    typ.entity_type
from with_stats as ws
left join registry as reg
    on ws.league_code = reg.league_code
left join types as typ
    on reg.competition_type = typ.competition_type
