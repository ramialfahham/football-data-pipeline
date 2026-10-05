{#
  A team-season equals the provider's league table wherever the table counts the same games: every
  table section of the team-season whose played equals our season_games_played must carry our wins,
  draws, losses, goals and goals against, and our points must equal 3 x the table's wins plus its
  draws. The table's own points equal that less the points the league took, declared with its
  source in seeds/standings_points_adjustments.csv. A table row with a different played count (a
  snapshot older than our last match, a section that counts other games) is not compared. A red row
  is a result or an adjustment to research and declare in the seeds, never an exception.

  Returns one row per disagreeing table row, with both sides.
#}
{{ config(store_failures = true, severity = 'error') }}

with ours as (
    select
        team_sk,
        season_sk,
        league_code,
        season_api_year,
        season_games_played,
        wins_sum_season as wins,
        draws_sum_season as draws,
        losses_sum_season as losses,
        goals,
        goals_against,
        points_won
    from {{ ref('int_team_season__metrics') }}
),

league_table as (
    select
        team_sk,
        season_sk,
        league_code,
        season_api_year,
        team_api_id,
        group_name,
        played,
        wins,
        draws,
        losses,
        goals_scored,
        goals_conceded,
        points
    from {{ ref('fct_standings') }}
),

adjustments as (
    select * from {{ ref('standings_points_adjustments') }}
)

select
    o.league_code,
    o.season_api_year,
    o.team_sk,
    t.group_name,
    o.season_games_played as played,
    o.wins,
    t.wins as table_wins,
    o.draws,
    t.draws as table_draws,
    o.losses,
    t.losses as table_losses,
    o.goals,
    t.goals_scored as table_goals,
    o.goals_against,
    t.goals_conceded as table_goals_against,
    o.points_won,
    3 * t.wins + t.draws as table_points_from_results,
    a.points_taken,
    t.points as table_points
from ours as o
inner join league_table as t
    on
        o.team_sk = t.team_sk
        and o.season_sk = t.season_sk
        and o.season_games_played = t.played
left join adjustments as a
    on
        t.league_code = a.league_code
        and t.season_api_year = a.season
        and t.team_api_id = a.team_id
        and trim(t.group_name) = trim(a.group_name)
where
    o.wins is distinct from t.wins
    or o.draws is distinct from t.draws
    or o.losses is distinct from t.losses
    or o.goals is distinct from t.goals_scored
    or o.goals_against is distinct from t.goals_conceded
    or o.points_won is distinct from 3 * t.wins + t.draws
    or t.points is distinct from 3 * t.wins + t.draws - coalesce(a.points_taken, 0)
