{{ config(materialized='table') }}

{#
  Whole-season team rollup — now the FINAL-ROW PROJECTION of int_team_season__metrics_cumulative
  (#500 one-aggregation; the rate formulas moved there, applied at every matchday). Per
  (league_code, season_api_year, team_sk): the last cumulative row of the season (max match_number)
  + the whole-season-only extras — team_season_sk and season_matchdays_used — re-attached here.

  Output is BYTE-IDENTICAL to the prior model (same formulas over the same input, same final row):
  every downstream consumer (mart_team_season / _insights / _profile / _record, the benchmark
  chain, deserved-vs-actual) is unchanged. mart_team_season_insights exposes only the latest
  season_api_year per league_code.

  Grain: (team_sk, season_sk).
#}

with cumulative as (
    select * from {{ ref('int_team_season__metrics_cumulative') }}
),

-- the season's final cumulative row = its greatest match_number (= latest kickoff, since
-- match_number is row_number over kickoff asc; the whole-season totals live here).
season_final as (
    select * from cumulative
    qualify row_number() over (
        partition by team_sk, league_code, season_api_year
        order by match_number desc
    ) = 1
),

-- distinct matchdays used across the whole season (round_name lives on the leg, not the
-- cumulative row) — a whole-season-only field, so it is attached here, not in the base model.
matchdays as (
    select
        team_sk,
        league_code,
        season_api_year,
        count(distinct round_name) as season_matchdays_used
    from {{ ref('int_legs__team_match') }}
    group by team_sk, league_code, season_api_year
)

select
    {{ dbt_utils.generate_surrogate_key(['sf.team_sk', 'sf.season_sk']) }} as team_season_sk,
    -- everything from the final cumulative row except its per-matchday grain key; the
    -- _sum_season / season_games_played names now denote the whole season (final matchday).
    sf.* except (match_number),
    md.season_matchdays_used
from season_final as sf
left join matchdays as md
    on
        sf.team_sk = md.team_sk
        and sf.league_code = md.league_code
        and sf.season_api_year = md.season_api_year
