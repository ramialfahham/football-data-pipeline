{#
  A team-season whose counts differ from the provider's league table is withheld. Where a table
  section counts the same games as our season (its played equals our games played), our wins,
  draws, losses, goals and goals against must equal the section's, and our points must equal the
  section's points plus the points the league took, declared with its source in
  seeds/standings_points_adjustments.csv. A table row with a different played count (a snapshot
  older than our last match, a section that counts other games) is not compared. Where they differ
  the results or the table are wrong and nothing says which, so int_team_season__metrics holds the
  team-season withheld: counts_withheld true and every season value blank.

  The disagreement is derived here from the legs and fct_standings, never from the flag, by the
  macro team_seasons_off_standings that assert_team_season_off_standings_answer_key pins to
  hand-written rows. Returns one row per disagreeing team-season that is not withheld, a flag that
  is not set, a value that is not blank, or a team-season missing from the model.
#}
{{ config(store_failures = true, severity = 'error') }}

with leg_counts as (
    {{ team_season_counts_from_legs(ref('int_legs__team_match')) }}
),

disagreeing as (
    {{ team_seasons_off_standings('leg_counts', ref('fct_standings'), ref('standings_points_adjustments')) }}
)

select
    d.team_sk,
    d.season_sk,
    d.reason,
    m.team_sk is not null as row_found,
    m.counts_withheld,
    m.season_games_played,
    m.wins_sum_season,
    m.draws_sum_season,
    m.losses_sum_season,
    m.goals,
    m.goals_against,
    m.points_won
from disagreeing as d
left join {{ ref('int_team_season__metrics') }} as m
    on d.team_sk = m.team_sk and d.season_sk = m.season_sk
where
    d.reason = 'counts_differ'
    and (
        m.team_sk is null
        or not coalesce(m.counts_withheld, false)
        or m.season_games_played is not null
        or m.wins_sum_season is not null
        or m.draws_sum_season is not null
        or m.losses_sum_season is not null
        or m.goals is not null
        or m.goals_against is not null
        or m.points_won is not null
    )
