{#
  Per-fixture player stat lines (#323). The player half of the match detail
  view: every player's stat line for one finished fixture, both sides. A
  projection of fct_fixture_player_stats plus player / team identity for
  display. The app reads this mart, never core.

  The stat line keeps the keys the export has always read. Its one derived
  value, passes_accuracy_percent, is the catalogue's pass accuracy over the
  player's own match (written by scripts/generate_metric_sql.py), as a whole
  percentage.

  Covers ALL finished fixtures that have player stats. Many competitions do
  not provide statistics_players from the API, so a fixture with no rows here
  is the COMMON case — the app must render "player stats not available for
  this match", not treat it as an error.

  Grain: (fixture_sk, team_sk, player_sk).
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
    s.minutes as minutes_played,
    s.is_captain,
    s.is_substitute,
    s.is_starter,
    s.offsides,
    s.shots as shots_total,
    s.shots_on_target as shots_on,
    s.goals as goals_total,
    s.goals_against,
    s.assists as goals_assists,
    s.saves,
    s.passes as passes_total,
    s.passes_key,
    cast(round(100 * r.passes_accuracy_player_pct) as int64) as passes_accuracy_percent,
    s.tackles as tackles_total,
    s.blocks as tackles_blocks,
    s.interceptions as tackles_interceptions,
    s.duels as duels_total,
    s.duels_won,
    s.dribbles as dribbles_attempts,
    s.dribbles_success,
    s.dribbles_against as dribbles_past,
    s.fouls_against as fouls_drawn,
    s.fouls as fouls_committed,
    s.cards_yellow,
    s.cards_red,
    s.penalties_won as penalty_won,
    s.penalties_committed as penalty_committed,
    s.penalties_scored as penalty_scored,
    s.penalties_missed as penalty_missed,
    s.penalties_saved as penalty_saved,
    s.team_sk = f.home_team_sk as is_home
from stats as s
inner join fixtures as f
    on s.fixture_sk = f.fixture_sk
inner join match_rates as r
    on s.fixture_sk = r.fixture_sk and s.team_sk = r.team_sk and s.player_sk = r.player_sk
left join players as p
    on s.player_sk = p.player_sk
left join teams as t
    on s.team_sk = t.team_sk
