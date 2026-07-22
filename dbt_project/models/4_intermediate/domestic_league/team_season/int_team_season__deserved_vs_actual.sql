{{ config(materialized='table') }}

{#
  TEAM deserved-vs-actual read (rank-space). One row per (team_sk, season_sk): the team's actual
  league position versus the position deserved by its shots-on-target difference.

  Method (CPO-locked): deserved signal = sot_difference_per_match (SoT for - against per match — the best
  non-outcome predictor of league position, Spearman +0.70). deserved_rank = rank teams by
  sot_difference_per_match within their league-season (descending; 1 = best). actual_rank = the league table
  rank. gap = actual_rank - deserved_rank, so POSITIVE = under-performing (results lag the process),
  NEGATIVE = over-performing. TEAM only; no xG.

  Composes int_team_season__metrics (the gated sot_difference_per_match — never recomputed here) and
  int_team_season__standings_primary (standing_rank = actual_rank). Availability handling lives
  upstream / here, never in the catalogue formula (formula-vs-availability ruling).

  Full-table coverage gate (CPO): the rank comparison is only valid against a complete, fully
  rankable table — so deserved_rank / sot_rank_gap are computed only for league-seasons where EVERY
  team has both a computable sot_difference_per_match (full SoT coverage) AND an actual league rank; otherwise
  they are NULL for every team in that league-season. No hardcoded competition filter: the standings
  join generically restricts the read to competitions that carry a full league table (a knockout cup
  has no standing_rank, so it is naturally non-rankable and nulls out).

  Grain: (team_sk, season_sk).
#}

with metrics as (
    select
        team_season_sk,
        team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        entity_type,
        sot_difference_per_match
    from {{ ref('int_team_season__metrics') }}
),

standings as (
    select
        team_sk,
        season_sk,
        standing_rank
    from {{ ref('int_team_season__standings_primary') }}
),

joined as (
    select
        m.team_season_sk,
        m.team_sk,
        m.league_sk,
        m.season_sk,
        m.league_code,
        m.season_api_year,
        m.entity_type,
        m.sot_difference_per_match,
        s.standing_rank as actual_rank
    from metrics as m
    left join standings as s
        on m.team_sk = s.team_sk and m.season_sk = s.season_sk
),

-- full-table coverage gate: a league-season is rankable only when EVERY team has both a computable
-- sot_difference_per_match (full SoT coverage) and an actual league rank.
coverage as (
    select
        league_code,
        season_sk,
        countif(sot_difference_per_match is null) as teams_missing_sot,
        countif(actual_rank is null) as teams_missing_rank
    from joined
    group by league_code, season_sk
),

gated as (
    select
        j.*,
        (c.teams_missing_sot = 0 and c.teams_missing_rank = 0) as league_season_rankable
    from joined as j
    inner join coverage as c
        on j.league_code = c.league_code and j.season_sk = c.season_sk
),

ranked as (
    select
        g.*,
        case
            when g.league_season_rankable
                then rank() over (
                    partition by g.league_code, g.season_sk
                    order by g.sot_difference_per_match desc
                )
        end as deserved_rank
    from gated as g
)

select
    team_season_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    entity_type,
    sot_difference_per_match,
    actual_rank,
    deserved_rank,
    -- positive = under-performing (actual position below deserved); null when not rankable
    actual_rank - deserved_rank as sot_rank_gap
from ranked
