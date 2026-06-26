{{ config(materialized='table') }}

{#
  W1 momentum-window list mart — team. The drill-down behind the momentum metrics
  (#323): the same window matches mart_team_momentum aggregates, exposed
  un-aggregated — one row per (upcoming fixture side, past match), newest first.
  window_type (last_5 / tournament_to_date / qualifiers, GAP-18) is carried from the
  selection; tournament windows are cumulative, so a side can have more than five rows.

  played_fixture_sk is the click-through key into mart_team_fixture_stats /
  mart_player_fixture_stats. has_team_stats / has_player_stats tell the app
  honestly whether that drill-down has data (player stats are missing for a
  meaningful share of matches — the common case, not rare). The flags are
  derived from the detail marts themselves (same-layer refs, the documented
  exception in layering.md) so "true" literally means "the drill-down query
  returns rows" — one definition, no drift.

  Grain: (upcoming_fixture_sk, team_sk, played_fixture_sk).
#}

with window_legs as (
    select * from {{ ref('int_team_momentum_window') }}
),

fixtures as (
    select
        fixture_sk,
        league_code,
        home_team_sk
    from {{ ref('fct_fixture') }}
),

opponents as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
),

team_stat_coverage as (
    select distinct
        fixture_sk,
        team_sk
    from {{ ref('mart_team_fixture_stats') }}
),

player_stat_coverage as (
    select distinct
        fixture_sk,
        team_sk
    from {{ ref('mart_player_fixture_stats') }}
)

select
    wl.upcoming_fixture_sk,
    wl.team_sk,
    f.league_code,
    wl.entity_type,
    wl.season_api_year,
    wl.window_type,
    wl.recency_rank,
    wl.leg_fixture_sk as played_fixture_sk,
    wl.leg_league_code as played_league_code,
    wl.leg_kickoff_datetime as played_kickoff_datetime,
    wl.leg_round_name as played_round_name,
    wl.home_away,
    wl.goals_for,
    wl.goals_against,
    wl.result,
    wl.opponent_team_sk,
    opp.team_name as opponent_name,
    opp.team_logo_url as opponent_logo_url,
    wl.team_sk = f.home_team_sk as is_home,
    tc.fixture_sk is not null as has_team_stats,
    pc.fixture_sk is not null as has_player_stats
from window_legs as wl
inner join fixtures as f
    on wl.upcoming_fixture_sk = f.fixture_sk
left join opponents as opp
    on wl.opponent_team_sk = opp.team_sk
left join team_stat_coverage as tc
    on
        wl.leg_fixture_sk = tc.fixture_sk
        and wl.team_sk = tc.team_sk
left join player_stat_coverage as pc
    on
        wl.leg_fixture_sk = pc.fixture_sk
        and wl.team_sk = pc.team_sk
