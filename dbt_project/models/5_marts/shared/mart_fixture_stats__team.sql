{{ config(materialized='table') }}

{#
  Per-fixture team stat line (#323). The detail view behind a match in the
  form-window list: the full team stat line for one finished fixture, both
  sides as two rows. Pure projection of fct_fixture_team_stats — no derived
  metrics — plus fixture metadata and team identity for display. The app reads
  this mart, never core.

  Covers ALL finished fixtures that have team stats, not just form-window
  matches: it is selection-free by design and serves the team/player profile
  surfaces (#324/#325) too. A fixture with no rows here has no team stats —
  the honest "not available" state.

  Grain: (fixture_sk, team_sk).
#}

with stats as (
    select *
    from {{ ref('fct_fixture_team_stats') }}
    -- The API sometimes returns a statistics block with every value NULL
    -- (e.g. WC qualifier fixtures). Core keeps those shell rows faithfully,
    -- but they are not stat lines — projecting them would render an all-NULL
    -- detail view instead of the honest "stats not available" empty state.
    where
        coalesce(
            shots_on_goal, shots_off_goal, shots_total, shots_blocked,
            shots_inside_box, shots_outside_box, fouls, corner_kicks, offsides,
            ball_possession_percent, yellow_cards, red_cards, goalkeeper_saves,
            passes_total, passes_accurate, passes_accuracy_percent
        ) is not null
),

fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        home_team_sk,
        goals_home,
        goals_away
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
)

select
    s.fixture_sk,
    s.team_sk,
    f.league_code,
    f.season_api_year,
    f.kickoff_datetime,
    f.round_name,
    t.team_name,
    t.team_logo_url,
    s.shots_on_goal,
    s.shots_off_goal,
    s.shots_total,
    s.shots_blocked,
    s.shots_inside_box,
    s.shots_outside_box,
    s.fouls,
    s.corner_kicks,
    s.offsides,
    s.ball_possession_percent,
    s.yellow_cards,
    s.red_cards,
    s.goalkeeper_saves,
    s.passes_total,
    s.passes_accurate,
    s.passes_accuracy_percent,
    s.team_sk = f.home_team_sk as is_home,
    if(s.team_sk = f.home_team_sk, f.goals_home, f.goals_away) as goals_for,
    if(s.team_sk = f.home_team_sk, f.goals_away, f.goals_home) as goals_against
from stats as s
inner join fixtures as f
    on s.fixture_sk = f.fixture_sk
left join teams as t
    on s.team_sk = t.team_sk
