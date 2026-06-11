{{ config(materialized='table') }}

{#
  Phase-relevant standings context per upcoming-fixture side (epic #361).

  The single home for "what is this team's table position going into this
  fixture?" — extracted so both the MVP's mart_matchday_insights and the v2
  fixtures export read it instead of each re-deriving the rank rules. Reads
  mart_standings (same-layer ref, like the momentum source in matchday_insights;
  see layering.md cross-layer rule).

  Rank is shown only where a single round-robin table applies for the fixture's
  own competition+season:
  - season_sk scopes to the fixture's competition, so no competition_type filter.
  - single-table guard: a team with >1 standings section that season (overlapping-
    table leagues, e.g. Argentina Apertura + Anual) gets NULL.
  - knockout guard: NULL for knockout rounds (is_knockout_round) — a table is not
    meaningful there.
  These two guards are exactly the rules previously inlined in matchday_insights;
  this model is now the single source.

  Covers ALL upcoming fixtures (not just next round) so the v2 export can use it
  for every fixture; matchday_insights joins the next-round subset.

  group_name is kept even for knockout rounds (it still says which group a team
  came from); the table-position fields (rank/points/played/form) are suppressed
  for knockout. Grain: (fixture_sk, team_sk).
#}

with upcoming as (
    select
        fixture_sk,
        season_sk,
        round_name,
        home_team_sk,
        away_team_sk
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

sides as (
    select
        fixture_sk,
        season_sk,
        round_name,
        home_team_sk as team_sk
    from upcoming

    union all

    select
        fixture_sk,
        season_sk,
        round_name,
        away_team_sk as team_sk
    from upcoming
),

-- A team's standing in its own competition+season, restricted to teams with
-- exactly one section that season (single round-robin table).
standings_unique as (
    select
        team_sk,
        season_sk,
        group_name,
        standing_rank,
        points,
        played,
        goals_diff,
        form
    from {{ ref('mart_standings') }}
    qualify count(*) over (partition by team_sk, season_sk) = 1
)

select
    s.fixture_sk,
    s.team_sk,
    s.season_sk,
    su.group_name,
    {{ is_knockout_round('s.round_name') }} as is_knockout,
    case when {{ is_knockout_round('s.round_name') }} then null else su.standing_rank end
        as league_rank,
    case when {{ is_knockout_round('s.round_name') }} then null else su.points end
        as standing_points,
    case when {{ is_knockout_round('s.round_name') }} then null else su.played end
        as standing_played,
    case when {{ is_knockout_round('s.round_name') }} then null else su.goals_diff end
        as standing_goals_diff,
    case when {{ is_knockout_round('s.round_name') }} then null else su.form end
        as standing_form
from sides as s
left join standings_unique as su
    on
        s.team_sk = su.team_sk
        and s.season_sk = su.season_sk
