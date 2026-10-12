{#
  Per-fixture player rows (#323). The player half of the match detail
  view: every player of one finished fixture, both sides, that the stat lines
  or the confirmed or researched team sheets name. A projection of
  fct_fixture_player_stats and fct_fixture_lineup plus player / team identity
  for display. The app reads
  this mart, never core.

  The stat line keeps the keys the export has always read. Its one derived
  value, passes_accuracy_percent, is the catalogue's pass accuracy over the
  player's own match (written by scripts/generate_metric_sql.py), as a whole
  percentage.

  Many competitions do not provide statistics_players from the API, so a row
  without a stat line (has_stat_line false) is common: its statistics are
  unavailable, never zero.

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
),

lineups as (
    select
        fixture_sk,
        team_sk,
        player_sk,
        is_starter,
        shirt_number,
        position_code,
        minute_on,
        minute_on_extra,
        minute_off,
        minute_off_extra,
        replaced_player_sk
    from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched')
),

appearances as (
    select
        lineups.minute_on,
        lineups.minute_on_extra,
        lineups.minute_off,
        lineups.minute_off_extra,
        lineups.replaced_player_sk,
        coalesce(stats.fixture_sk, lineups.fixture_sk) as fixture_sk,
        coalesce(stats.team_sk, lineups.team_sk) as team_sk,
        coalesce(stats.player_sk, lineups.player_sk) as player_sk,
        stats.player_sk is not null as has_stat_line,
        coalesce(stats.position_code, lineups.position_code) as position_code,
        coalesce(stats.shirt_number, lineups.shirt_number) as shirt_number,
        if(lineups.player_sk is not null, not lineups.is_starter, stats.is_substitute) as is_substitute,
        if(lineups.player_sk is not null, lineups.is_starter, stats.is_starter) as is_starter
    from stats
    full outer join lineups
        on
            stats.fixture_sk = lineups.fixture_sk
            and stats.player_sk = lineups.player_sk
)

select
    a.fixture_sk,
    a.team_sk,
    a.player_sk,
    f.league_code,
    f.season_api_year,
    f.kickoff_datetime,
    f.round_name,
    t.team_name,
    p.player_name,
    p.player_photo_url,
    a.has_stat_line,
    a.position_code,
    a.shirt_number,
    s.minutes as minutes_played,
    s.is_captain,
    a.is_substitute,
    a.is_starter,
    a.minute_on,
    a.minute_on_extra,
    a.minute_off,
    a.minute_off_extra,
    a.replaced_player_sk,
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
    a.team_sk = f.home_team_sk as is_home
from appearances as a
inner join fixtures as f
    on a.fixture_sk = f.fixture_sk
left join stats as s
    on a.fixture_sk = s.fixture_sk and a.team_sk = s.team_sk and a.player_sk = s.player_sk
left join match_rates as r
    on a.fixture_sk = r.fixture_sk and a.team_sk = r.team_sk and a.player_sk = r.player_sk
left join players as p
    on a.player_sk = p.player_sk
left join teams as t
    on a.team_sk = t.team_sk
