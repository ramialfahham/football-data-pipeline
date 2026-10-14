{#
  A player's numbers in one played match: the match window, a window of one. One row per player per
  played match with a stat line, carrying the count metrics the played match page's Match leaders
  boards rank (mart_leaderboards, window_type match).

  Grain: (fixture_sk, player_sk).

  The window is the match itself, so every row is complete: a stat line exists only where the
  team's match has player data. Every metric is its catalogue formula over that one row, written by
  scripts/generate_metric_sql.py by the rules in models/docs/metric_rules.md.
#}

with legs as (
    select * from {{ ref('int_legs__player_match') }}
),

window_rows as (
    select
        legs.*,
        true as window_is_complete
    from legs
)

select
    fixture_sk,
    player_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    kickoff_datetime,
    if(logical_and(window_is_complete and minutes is not null), sum(minutes), null) as minutes,
    -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
    if(logical_and(window_is_complete and shots is not null), sum(shots), null) as shots_player,
    if(logical_and(window_is_complete and passes is not null), sum(passes), null) as passes_player,
    if(logical_and(window_is_complete and passes_key is not null), sum(passes_key), null) as passes_key_player,
    if(logical_and(window_is_complete and dribbles is not null), sum(dribbles), null) as dribbles_attempts_player,
    if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null) as duels_won_player,
    if(
        logical_and(window_is_complete and (tackles + interceptions + blocks) is not null),
        sum(tackles + interceptions + blocks),
        null
    ) as defensive_actions_player,
    if(logical_and(window_is_complete and fouls is not null), sum(fouls), null) as fouls_player
    -- end of generated metric sql
from window_rows
group by fixture_sk, player_sk, team_sk, league_sk, season_sk, league_code, season_api_year, kickoff_datetime
