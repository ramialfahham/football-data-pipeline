{#
  The team-seasons whose results disagree with the provider's standings. One row per team-season and
  reason, two reasons:
    counts_differ - a standings row that counts the same games as our season (its played equals our
        games played) carries other wins, draws, losses, goals or goals against, or other points
        than ours plus the points the league took, declared in standings_points_adjustments;
    games_short - our games played are fewer than the most any standings row of the team-season
        counts. The maximum is used because one team-season can hold several standings rows (a
        group table and a play-off table) that count different numbers of games, and any one of
        them says the team played that many.
  A standings row that counts other games, a snapshot older than our last match or a section that
  counts other games, is not compared: ours being ahead of it is the normal state.

  counts: a relation with team_sk, season_sk, season_games_played, wins, draws, losses, goals,
      goals_against and points_won, one row per team-season.
  standings: a relation with team_sk, season_sk, league_code, season_api_year, team_api_id,
      group_name, played, wins, draws, losses, goals_scored, goals_conceded and points.
  adjustments: a relation with league_code, season, team_id, group_name and points_taken.
  Returns a select, so call it inside a CTE or a subquery.
#}
{% macro team_seasons_off_standings(counts, standings, adjustments) -%}
    with off_adjusted as (
        select
            league_code,
            season,
            team_id,
            trim(group_name) as group_name,
            sum(points_taken) as points_taken
        from {{ adjustments }}
        group by league_code, season, team_id, trim(group_name)
    ),

    off_same_games as (
        select distinct
            o.team_sk,
            o.season_sk,
            'counts_differ' as reason
        from {{ counts }} as o
        inner join {{ standings }} as t
            on
                o.team_sk = t.team_sk
                and o.season_sk = t.season_sk
                and o.season_games_played = t.played
        left join off_adjusted as a
            on
                t.league_code = a.league_code
                and t.season_api_year = a.season
                and t.team_api_id = a.team_id
                and trim(t.group_name) = a.group_name
        where
            o.wins is distinct from t.wins
            or o.draws is distinct from t.draws
            or o.losses is distinct from t.losses
            or o.goals is distinct from t.goals_scored
            or o.goals_against is distinct from t.goals_conceded
            or o.points_won is distinct from t.points + coalesce(a.points_taken, 0)
    ),

    off_most_played as (
        select
            team_sk,
            season_sk,
            max(played) as played
        from {{ standings }}
        group by team_sk, season_sk
    ),

    off_short as (
        select distinct
            o.team_sk,
            o.season_sk,
            'games_short' as reason
        from {{ counts }} as o
        inner join off_most_played as s
            on o.team_sk = s.team_sk and o.season_sk = s.season_sk
        where s.played is not null and o.season_games_played < s.played
    )

    select * from off_same_games
    union all
    select * from off_short
{%- endmacro %}
