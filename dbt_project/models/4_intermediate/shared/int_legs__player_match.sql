{{ config(materialized='table') }}

{#
  Building-block player-match leg: one row per (player, finished match) with that player's
  raw counts, plus the competition's type/entity classification and the dimensions windows
  need. Cross-competition and cross-type — the shared foundation every player performance
  metric aggregates over. Grain: (fixture_sk, player_sk).

  Restricted to finished matches (FT/AET/PEN) with a valid scoreline, matching the team leg.
  Note: player stats have large coverage gaps (many competitions lack statistics_players),
  so this is naturally sparse — absence is honest, not an error.
#}

with player_stats as (
    select * from {{ ref('fct_fixture_player_stats') }}
),

fixtures as (
    select * from {{ ref('fct_fixture') }}
),

registry as (
    select * from {{ ref('competition_registry') }}
),

types as (
    select * from {{ ref('competition_types') }}
),

finished as (
    select
        fixture_sk,
        season_api_year,
        kickoff_datetime,
        round_name,
        home_team_sk,
        away_team_sk
    from fixtures
    where
        status_short in ('FT', 'AET', 'PEN')
        and goals_home is not null
        and goals_away is not null
)

select
    ps.fixture_sk,
    ps.player_sk,
    ps.team_sk,
    ps.league_code,
    f.season_api_year,
    f.kickoff_datetime,
    f.round_name,
    reg.competition_type,
    typ.entity_type,
    ps.minutes_played,
    ps.rating,
    ps.is_starter,
    ps.is_substitute,
    ps.position_code,
    ps.shots_total,
    ps.shots_on,
    ps.goals_total,
    ps.goals_conceded,
    ps.goals_assists,
    ps.goals_saves,
    ps.passes_total,
    ps.passes_key,
    ps.passes_accuracy_percent,
    ps.tackles_total,
    ps.tackles_blocks,
    ps.tackles_interceptions,
    ps.duels_total,
    ps.duels_won,
    ps.dribbles_attempts,
    ps.dribbles_success,
    ps.offsides,
    ps.fouls_drawn,
    ps.fouls_committed,
    ps.cards_yellow,
    ps.cards_red,
    ps.dribbles_past,
    ps.penalty_won,
    ps.penalty_committed,
    safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
    case when ps.team_sk = f.home_team_sk then f.away_team_sk else f.home_team_sk end
        as opponent_team_sk,
    case when ps.team_sk = f.home_team_sk then 'home' else 'away' end as home_away
from player_stats as ps
inner join finished as f
    on ps.fixture_sk = f.fixture_sk
left join registry as reg
    on ps.league_code = reg.league_code
left join types as typ
    on reg.competition_type = typ.competition_type
