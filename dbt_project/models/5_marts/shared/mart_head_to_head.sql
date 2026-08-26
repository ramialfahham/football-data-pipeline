{{ config(materialized='table') }}

{#
  Head-to-head (#375). All-time past meetings between two teams, DIRECTED: one
  row per (team_sk, opponent_team_sk) = that team's record against that opponent.
  The fixture page looks up (home_team_sk, away_team_sk) directly to get the home
  side's record; the mirror row carries the away side's.

  Built from int_legs__team_match — the directed team-match leg is already the
  right grain (team + opponent + result per finished match). A normal
  core -> intermediate -> mart build, NOT mart-from-mart.

  Raw record facts only — meetings, W/D/L, goals, last-5 splits, last meeting,
  and a recent_meetings array. No derived performance ratios.

  W/D/L are match RESULTS tallied over the pair, not metrics, and stay out of the
  catalogue for that reason. `goals_for` / `goals_against` ARE catalogue metrics —
  sum(goals_for) below is the catalogue's own formula, run over the head-to-head
  window instead of a season, and a different window is not a different metric.
  What stays out is a ratio invented for this mart alone
  (see feedback_metric_catalogue_governance).

  Scope: all finished meetings across ALL competitions between the pair (the
  all-time H2H). Competition-scoped H2H is a later refinement. A pair that has
  never met produces no row (the fixture page shows "no previous meetings").

  Grain: (team_sk, opponent_team_sk).
#}

with legs as (
    select
        team_sk,
        opponent_team_sk,
        fixture_sk,
        league_code,
        kickoff_datetime,
        goals_for,
        goals_against,
        result
    from {{ ref('int_legs__team_match') }}
    where opponent_team_sk is not null
),

ranked as (
    select
        team_sk,
        opponent_team_sk,
        fixture_sk,
        league_code,
        kickoff_datetime,
        goals_for,
        goals_against,
        result,
        row_number() over (
            partition by team_sk, opponent_team_sk
            order by kickoff_datetime desc, fixture_sk desc
        ) as recency_rank
    from legs
),

last_meeting as (
    select
        team_sk,
        opponent_team_sk,
        kickoff_datetime as last_meeting_at,
        league_code as last_meeting_league_code,
        goals_for as last_meeting_goals_for,
        goals_against as last_meeting_goals_against,
        result as last_meeting_result
    from ranked
    where recency_rank = 1
),

agg as (
    select
        team_sk,
        opponent_team_sk,
        count(*) as total_meetings,
        countif(result = 'W') as wins,
        countif(result = 'D') as draws,
        countif(result = 'L') as losses,
        sum(goals_for) as goals_for,
        sum(goals_against) as goals_against,
        countif(recency_rank <= 5) as meetings_last5,
        countif(recency_rank <= 5 and result = 'W') as wins_last5,
        countif(recency_rank <= 5 and result = 'D') as draws_last5,
        countif(recency_rank <= 5 and result = 'L') as losses_last5,
        array_agg(
            struct(
                kickoff_datetime,
                league_code,
                goals_for,
                goals_against,
                result
            )
            order by recency_rank
            limit 10
        ) as recent_meetings
    from ranked
    group by
        team_sk,
        opponent_team_sk
)

select
    a.team_sk,
    a.opponent_team_sk,
    a.total_meetings,
    a.wins,
    a.draws,
    a.losses,
    a.goals_for,
    a.goals_against,
    a.meetings_last5,
    a.wins_last5,
    a.draws_last5,
    a.losses_last5,
    lm.last_meeting_at,
    lm.last_meeting_league_code,
    lm.last_meeting_goals_for,
    lm.last_meeting_goals_against,
    lm.last_meeting_result,
    a.recent_meetings,
    -- canonical pair identity for the /h2h/ URL (GAP-19.4): lower id first, so both
    -- directed rows share one key; is_canonical marks the lower-id direction (one row
    -- per unordered pair). opponent_team_sk is non-null (filtered in legs).
    concat(
        cast(least(a.team_sk, a.opponent_team_sk) as string),
        '-',
        cast(greatest(a.team_sk, a.opponent_team_sk) as string)
    ) as pair_key,
    a.team_sk < a.opponent_team_sk as is_canonical
from agg as a
left join last_meeting as lm
    on
        a.team_sk = lm.team_sk
        and a.opponent_team_sk = lm.opponent_team_sk
