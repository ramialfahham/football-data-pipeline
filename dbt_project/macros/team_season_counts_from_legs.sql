{#
  A team-season's counts built from its legs, the inputs team_seasons_off_standings compares with the
  provider's standings: games played, wins, draws, losses, goals, goals against and points. The
  rules are those of int_team_season__metrics_cumulative for the whole season: a count is blank when
  one match of the season has no value for it, and the points are three per win and one per draw plus
  the matches the table counts as won on a shoot-out.

  legs: a relation with one row per team-match leg (int_legs__team_match): team_sk, season_sk,
      result, goals, goals_against and is_table_shootout_win.
  Returns a select, so call it inside a CTE or a subquery.
#}
{% macro team_season_counts_from_legs(legs) -%}
    select
        team_sk,
        season_sk,
        count(*) as season_games_played,
        countif(result = 'W') as wins,
        countif(result = 'D') as draws,
        countif(result = 'L') as losses,
        if(logical_and(goals is not null), sum(goals), null) as goals,
        if(logical_and(goals_against is not null), sum(goals_against), null) as goals_against,
        sum(case result when 'W' then 3 when 'D' then 1 else 0 end)
        + if(logical_and(is_table_shootout_win is not null), countif(is_table_shootout_win), null) as points_won
    from {{ legs }}
    group by team_sk, season_sk
{%- endmacro %}
