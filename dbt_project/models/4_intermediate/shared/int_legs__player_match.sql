{#
  Building-block player-match leg: one row per (player, finished match) with that player's
  cleaned counts, plus the competition's type/entity classification and the dimensions windows
  need. Cross-competition and cross-type — the shared foundation every player performance
  metric aggregates over, and the base_relation of every player formula in metric_catalogue.csv.
  Grain: (fixture_sk, player_sk).

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

competitions as (
    select * from {{ ref('dim_league') }}
),

-- The stat line files some bench players as starters; a checked team sheet says who was on the bench.
checked_sheets as (
    select
        fixture_sk,
        player_sk,
        is_starter
    from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched')
),

player_bench as (
    select
        ps.*,
        if(sheet.player_sk is not null, not sheet.is_starter, ps.is_substitute) as is_substitute_checked
    from player_stats as ps
    left join checked_sheets as sheet
        on ps.fixture_sk = sheet.fixture_sk and ps.player_sk = sheet.player_sk
),

player_roles as (
    select
        *,
        coalesce(minutes, 0) > 0 and not coalesce(is_substitute_checked, false) as is_starter_checked
    from player_bench
),

finished as (
    select
        fixture_sk,
        league_sk,
        season_sk,
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
    f.league_sk,
    f.season_sk,
    f.season_api_year,
    f.kickoff_datetime,
    f.round_name,
    reg.competition_type,
    reg.entity_type,
    ps.is_from_lineups,
    ps.minutes,
    ps.is_starter_checked as is_starter,
    ps.is_substitute_checked as is_substitute,
    ps.position_code,
    ps.shots,
    ps.shots_on_target,
    ps.goals,
    ps.goals_penalty,
    ps.goals_against,
    ps.goals_own_against,
    ps.assists,
    ps.saves,
    ps.passes,
    ps.passes_key,
    ps.passes_accurate,
    ps.tackles,
    ps.blocks,
    ps.interceptions,
    ps.duels,
    ps.duels_won,
    ps.dribbles,
    ps.dribbles_success,
    ps.offsides,
    ps.fouls_against,
    ps.fouls,
    ps.cards_yellow,
    ps.cards_red,
    ps.dribbles_against,
    ps.penalties_won,
    ps.penalties_committed,
    safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
    case when ps.team_sk = f.home_team_sk then f.away_team_sk else f.home_team_sk end
        as opponent_team_sk,
    case when ps.team_sk = f.home_team_sk then 'home' else 'away' end as home_away
from player_roles as ps
inner join finished as f
    on ps.fixture_sk = f.fixture_sk
left join competitions as reg
    on ps.league_code = reg.league_code
