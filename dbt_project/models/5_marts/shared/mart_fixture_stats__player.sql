{{ config(materialized='table') }}

{#
  Per-fixture player stat lines (#323). The player half of the match detail
  view: every player's stat line for one finished fixture, both sides. Pure
  projection of fct_fixture_player_stats — no derived metrics — plus player /
  team identity for display. The app reads this mart, never core.

  Covers ALL finished fixtures that have player stats. Many competitions do
  not provide statistics_players from the API, so a fixture with no rows here
  is the COMMON case — the app must render "player stats not available for
  this match", not treat it as an error.

  Grain: (fixture_sk, team_sk, player_sk).
#}

with stats as (
    select * from {{ ref('fct_fixture_player_stats') }}
),

fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        home_team_sk
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

players as (
    select
        player_sk,
        player_name,
        player_photo_url
    from {{ ref('dim_player') }}
),

teams as (
    select
        team_sk,
        team_name
    from {{ ref('dim_team') }}
)

select
    s.fixture_sk,
    s.team_sk,
    s.player_sk,
    f.league_code,
    f.season_api_year,
    f.kickoff_datetime,
    f.round_name,
    t.team_name,
    p.player_name,
    p.player_photo_url,
    s.position_code,
    s.shirt_number,
    s.minutes_played,
    s.is_captain,
    s.is_substitute,
    s.is_starter,
    s.offsides,
    s.shots_total,
    s.shots_on,
    s.goals_total,
    s.goals_conceded,
    s.goals_assists,
    s.goals_saves,
    s.passes_total,
    s.passes_key,
    s.passes_accuracy_percent,
    s.tackles_total,
    s.tackles_blocks,
    s.tackles_interceptions,
    s.duels_total,
    s.duels_won,
    s.dribbles_attempts,
    s.dribbles_success,
    s.dribbles_past,
    s.fouls_drawn,
    s.fouls_committed,
    s.cards_yellow,
    s.cards_red,
    s.penalty_won,
    s.penalty_committed,
    s.penalty_scored,
    s.penalty_missed,
    s.penalty_saved,
    s.team_sk = f.home_team_sk as is_home
from stats as s
inner join fixtures as f
    on s.fixture_sk = f.fixture_sk
left join players as p
    on s.player_sk = p.player_sk
left join teams as t
    on s.team_sk = t.team_sk
