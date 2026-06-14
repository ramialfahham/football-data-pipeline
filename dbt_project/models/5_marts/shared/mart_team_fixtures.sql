{{ config(materialized='view') }}

{#
  Team fixtures (GAP-15). One row per (team, fixture), team perspective: the
  team-profile page's "next fixture + recent results" surface.

  Spine: fct_fixture, unpivoted to two team-perspective rows per fixture (home +
  away). The opponent's identity (name, crest) comes from dim_team. Finished
  results (goals_for/against, W/D/L) are taken from the tested perspective leg
  int_legs__team_match — NOT re-derived here (consumption-layer contract). Rank
  columns make the consumption pure selection: upcoming_rank = 1 is the next
  fixture, recency_rank <= 5 the last five results — no window logic in any
  frontend.

  Rows exist for every fixture; ranks are populated only for scheduled (NS/TBD)
  and finished-with-leg fixtures. Live / postponed / cancelled rows carry null
  ranks (no honest place in "next" or "recent results").

  No slug column: the published fixture URL identity is a separate, CPO-ruled
  concern (GAP-19 item 5) and is added in its own PR. league_code is the
  partition key; the model is competition-agnostic.

  Grain: (team_sk, fixture_sk).
#}

with fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        status_short,
        home_team_sk,
        away_team_sk
    from {{ ref('fct_fixture') }}
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
),

legs as (
    select
        team_sk,
        fixture_sk,
        goals_for,
        goals_against,
        result
    from {{ ref('int_legs__team_match') }}
),

-- each fixture as two team-perspective rows (home side, away side)
sides as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        status_short,
        home_team_sk as team_sk,
        away_team_sk as opponent_team_sk,
        true as is_home
    from fixtures
    union all
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        status_short,
        away_team_sk as team_sk,
        home_team_sk as opponent_team_sk,
        false as is_home
    from fixtures
),

joined as (
    select
        s.team_sk,
        s.fixture_sk,
        s.league_code,
        s.season_api_year,
        s.kickoff_datetime,
        s.round_name,
        s.status_short,
        s.is_home,
        s.opponent_team_sk,
        t.team_name as opponent_name,
        t.team_logo_url as opponent_logo_url,
        l.goals_for,
        l.goals_against,
        l.result,
        -- has_result = a tested result leg exists (int_legs requires FT/AET/PEN with
        -- non-null scores). This — not raw status — is the honest "show in recent
        -- results" population; a finished fixture with null scores has no leg.
        l.fixture_sk is not null as has_result,
        s.status_short in ('NS', 'TBD') as is_upcoming
    from sides as s
    left join teams as t
        on s.opponent_team_sk = t.team_sk
    left join legs as l
        on
            s.fixture_sk = l.fixture_sk
            and s.team_sk = l.team_sk
    where s.team_sk is not null
)

select
    team_sk,
    fixture_sk,
    league_code,
    season_api_year,
    kickoff_datetime,
    round_name,
    status_short,
    is_home,
    opponent_team_sk,
    opponent_name,
    opponent_logo_url,
    goals_for,
    goals_against,
    result,
    has_result,
    is_upcoming,
    -- selection ranks: the eligibility flag is IN partition by, so each rank is dense
    -- within its own population (1..n) and no rank is consumed by an ineligible row
    case
        when is_upcoming then row_number() over (
            partition by team_sk, league_code, season_api_year, is_upcoming
            order by kickoff_datetime asc, fixture_sk asc
        )
    end as upcoming_rank,
    case
        when has_result then row_number() over (
            partition by team_sk, league_code, season_api_year, has_result
            order by kickoff_datetime desc, fixture_sk desc
        )
    end as recency_rank
from joined
