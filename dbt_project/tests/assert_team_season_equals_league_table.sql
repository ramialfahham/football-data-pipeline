{#
  A team-season equals the provider's league table wherever the table counts the same games: every
  table section of the team-season whose played equals our season_games_played must carry our wins,
  draws, losses, goals and goals against, and our points must equal 3 x the table's wins plus its
  draws. The table's own points can be lower than that by a deduction or a halving, which is the
  league's adjustment, and never higher or blank. A table row with a different played count (a snapshot older than our last
  match, a section that counts other games) is not compared. A red row is a result to research and
  correct in the correction seeds, never an exception.

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
        group_name,
        played,
        wins,
        draws,
        losses,
        goals_scored,
        goals_conceded,
        points
    from {{ ref('fct_standings') }}
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
    t.points as table_points
from ours as o
inner join league_table as t
    on
        o.team_sk = t.team_sk
        and o.season_sk = t.season_sk
        and o.season_games_played = t.played
where
    o.wins is distinct from t.wins
    or o.draws is distinct from t.draws
    or o.losses is distinct from t.losses
    or o.goals is distinct from t.goals_scored
    or o.goals_against is distinct from t.goals_conceded
    or o.points_won is distinct from 3 * t.wins + t.draws
    or t.points is null
    or t.points > 3 * t.wins + t.draws
