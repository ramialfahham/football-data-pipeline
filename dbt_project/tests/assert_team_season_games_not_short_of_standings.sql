{#
  A team-season with fewer played games than its standings say is withheld. Our count of a team's
  played matches must never be LOWER than the number the competition's own standings say it played:
  when it is, a match a governing body records as played is missing from our legs, whatever the
  cause (a fixture stuck at SUSP or INT, one mislabelled CANC, one awarded and filed under a status
  nothing reads, one the provider never published). The standings' played count is produced
  independently of the status field, so this catches the symptom, not a list of causes. Then the
  provider's results or its standings are wrong and nothing says which, so int_team_season__metrics
  holds the team-season withheld: counts_withheld true and every season value blank.

  One direction only, because being ahead of the standings is the normal state: standings are a
  snapshot taken when they were last ingested and we count fixtures afterwards. Measured over 4,082
  team-seasons: 2,515 agree, 1,564 have our count higher by 1 to 30 games, 3 have it lower. The
  standings' played count is the largest of the team-season's standings rows, because one team-season
  can hold a group table and a play-off table that count different numbers of games (299
  team-seasons, 204 of them disagreeing on played by up to 13 games); any one of them says the team
  played that many. The standings are read from fct_standings directly, because
  int_team_season__standings_primary keeps one row for display.

  The disagreement is derived here from the legs and fct_standings, never from the flag, by the
  macro team_seasons_off_standings that assert_team_season_off_standings_answer_key pins to
  hand-written rows. Returns one row per team-season short of its standings that is not withheld, a
  flag that is not set, a value that is not blank, or a team-season missing from the model.
#}
{{
    config(
        severity = 'error',
        tags=["dq", "core", "season_reconciliation"],
        store_failures = true
    )
}}

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
    d.reason = 'games_short'
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
