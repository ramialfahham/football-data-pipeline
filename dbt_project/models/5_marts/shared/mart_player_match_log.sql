{#
  Player match log (#325). One row per (player, finished fixture): the player's
  stat line for that match plus the match context (opponent, score, result from
  the player's team's perspective). Feeds the match-by-match table on the player
  profile page; the UI orders by kickoff and slices the window (last 5 / season).

  Distinct from mart_player_fixture_stats (#323): that is fixture-detail-shaped
  (both teams' lines for one fixture); this is player-history-shaped (one player's
  matches over time, with opponent + result attached).

  The stat line keeps the keys the export has always read. passes_accuracy_percent
  is the catalogue's pass accuracy over the player's own match (written by
  scripts/generate_metric_sql.py), as a whole percentage.

  Grain: (player_sk, fixture_sk).
#}

with stats as (
    select
        *,
        true as window_is_complete
    from {{ ref('fct_fixture_player_stats') }}
),

match_rates as (
    select
        fixture_sk,
        team_sk,
        player_sk,
        -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
        safe_divide(
            if(
                logical_and(window_is_complete and passes_accurate is not null) over w,
                sum(passes_accurate) over w,
                null
            ),
            if(
                logical_and(window_is_complete and passes is not null) over w,
                sum(passes) over w,
                null
            )
        ) as passes_accuracy_player_pct
        -- end of generated metric sql
    from stats
    window w as (partition by fixture_sk, team_sk, player_sk)
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
        s.minutes as minutes_played,
        s.is_starter,
        s.is_substitute,
        s.goals as goals_total,
        s.assists as goals_assists,
        s.saves,
        s.shots as shots_total,
        s.shots_on_target as shots_on,
        s.passes as passes_total,
        s.passes_key,
        cast(round(100 * r.passes_accuracy_player_pct) as int64) as passes_accuracy_percent,
        s.tackles as tackles_total,
        s.interceptions as tackles_interceptions,
        s.duels as duels_total,
        s.duels_won,
        s.dribbles as dribbles_attempts,
        s.dribbles_success,
        s.fouls_against as fouls_drawn,
        s.fouls as fouls_committed,
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
    inner join match_rates as r
        on s.fixture_sk = r.fixture_sk and s.team_sk = r.team_sk and s.player_sk = r.player_sk
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
    j.goals_total,
    j.goals_assists,
    j.saves,
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
