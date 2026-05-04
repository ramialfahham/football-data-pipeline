-- Deduplicated league-season rows. Multiple ingestion runs produce duplicate
-- rows for the same (league_code, league_api_id, season_api_year); this model
-- keeps only the most recently ingested version of each.
-- Output grain: (league_code, league_api_id, season_api_year).

with src as (
    select
        league_code,
        league_api_id,
        league_name,
        league_type,
        country as league_country,
        league_logo_url,
        country_flag_url,
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
    from {{ ref('stg_apif__bl1_leagues') }}
    where
        league_api_id is not null
        and season_api_year is not null
),

deduped as (
    select
        *,
        row_number() over (
            partition by league_code, league_api_id, season_api_year
            order by raw_ingested_at desc
        ) as rn
    from src
)

select
    league_code,
    league_api_id,
    league_name,
    league_type,
    league_country,
    league_logo_url,
    country_flag_url,
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
from deduped
where rn = 1
