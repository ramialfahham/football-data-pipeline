{{ config(materialized='table') }}

{#
  Player match log (#325). One row per (player, finished fixture): the player's
  stat line for that match plus the match context (opponent, score, result from
  the player's team's perspective). Feeds the match-by-match table on the player
  profile page; the UI orders by kickoff and slices the window (last 5 / season).

  Distinct from mart_fixture_stats__player (#323): that is fixture-detail-shaped
  (both teams' lines for one fixture); this is player-history-shaped (one player's
  matches over time, with opponent + result attached).

  Grain: (player_sk, fixture_sk).
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
        home_team_sk,
        away_team_sk,
        goals_home,
        goals_away
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
),

players as (
    select
        player_sk,
        player_name,
        player_photo_url
    from {{ ref('dim_player') }}
),

joined as (
    select
        s.player_sk,
        s.fixture_sk,
        s.team_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.round_name,
        f.home_team_sk,
        f.away_team_sk,
        f.goals_home,
        f.goals_away,
        s.position_code,
        s.minutes_played,
        s.is_starter,
        s.is_substitute,
        s.rating,
        s.goals_total,
        s.goals_assists,
        s.goals_conceded,
        s.goals_saves,
        s.shots_total,
        s.shots_on,
        s.passes_total,
        s.passes_key,
        s.passes_accuracy_percent,
        s.tackles_total,
        s.tackles_interceptions,
        s.duels_total,
        s.duels_won,
        s.dribbles_attempts,
        s.dribbles_success,
        s.fouls_drawn,
        s.fouls_committed,
        s.cards_yellow,
        s.cards_red,
        s.team_sk = f.home_team_sk as is_home,
        if(s.team_sk = f.home_team_sk, f.away_team_sk, f.home_team_sk)
            as opponent_team_sk,
        if(s.team_sk = f.home_team_sk, f.goals_home, f.goals_away) as goals_for,
        if(s.team_sk = f.home_team_sk, f.goals_away, f.goals_home) as goals_against
    from stats as s
    inner join fixtures as f
        on s.fixture_sk = f.fixture_sk
)

select
    j.player_sk,
    j.fixture_sk,
    j.team_sk,
    j.opponent_team_sk,
    j.league_code,
    j.season_api_year,
    j.kickoff_datetime,
    j.round_name,
    j.is_home,
    j.goals_for,
    j.goals_against,
    pl.player_name,
    pl.player_photo_url,
    t.team_name,
    t.team_logo_url,
    opp.team_name as opponent_name,
    opp.team_logo_url as opponent_logo_url,
    j.position_code,
    j.minutes_played,
    j.is_starter,
    j.is_substitute,
    j.rating,
    j.goals_total,
    j.goals_assists,
    j.goals_conceded,
    j.goals_saves,
    j.shots_total,
    j.shots_on,
    j.passes_total,
    j.passes_key,
    j.passes_accuracy_percent,
    j.tackles_total,
    j.tackles_interceptions,
    j.duels_total,
    j.duels_won,
    j.dribbles_attempts,
    j.dribbles_success,
    j.fouls_drawn,
    j.fouls_committed,
    j.cards_yellow,
    j.cards_red,
    case
        when j.goals_for > j.goals_against then 'W'
        when j.goals_for < j.goals_against then 'L'
        else 'D'
    end as result
from joined as j
left join players as pl
    on j.player_sk = pl.player_sk
left join teams as t
    on j.team_sk = t.team_sk
left join teams as opp
    on j.opponent_team_sk = opp.team_sk
