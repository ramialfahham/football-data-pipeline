{{ config(materialized='table') }}

with leagues_src as (
    select
        league_code,
        league_api_id,
        raw_ingested_at,
        season_api_year,
        season_start_date,
        season_end_date,
        season_is_current,
        has_coverage_fixture_events,
        has_coverage_fixture_lineups,
        has_coverage_fixture_statistics,
        has_coverage_fixture_players,
        has_coverage_standings,
        has_coverage_players,
        has_coverage_top_scorers,
        has_coverage_top_assists,
        has_coverage_top_cards,
        has_coverage_injuries,
        has_coverage_predictions,
        has_coverage_odds
    from {{ ref('stg_apif__d1_leagues') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by league_code, season_api_year
            order by raw_ingested_at desc
        ) as rn
    from leagues_src
    where season_api_year is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'season_api_year']) }} as season_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'league_api_id']) }} as league_sk,
    league_code,
    season_api_year,
    season_start_date,
    season_end_date,
    season_is_current,
    has_coverage_fixture_events,
    has_coverage_fixture_lineups,
    has_coverage_fixture_statistics,
    has_coverage_fixture_players,
    has_coverage_standings,
    has_coverage_players,
    has_coverage_top_scorers,
    has_coverage_top_assists,
    has_coverage_top_cards,
    has_coverage_injuries,
    has_coverage_predictions,
    has_coverage_odds,
    raw_ingested_at
from ranked
where rn = 1
