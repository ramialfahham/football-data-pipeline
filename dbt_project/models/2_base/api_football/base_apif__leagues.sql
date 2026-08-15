with import_stg_apif__leagues as (
    select * from {{ ref('stg_apif__leagues') }}
),

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

-- The provider's country string is not display-ready: it hyphenates multi-word names
-- (Saudi-Arabia, South-Korea) and abbreviates one (USA). Standardised HERE, in base, because
-- the transformation layer is where we clean and reconcile (CPO 2026-08-14) and because the
-- core dim publishes rather than corrects -- there is no coalesce in dim_league. Same three
-- parts as team_name_overrides: seed, left join, and a singular test that fails when a row
-- stops being a correction.
src as (
    select
        leagues.league_code,
        leagues.league_api_id,
        leagues.league_name,
        leagues.league_type,
        leagues.league_logo_url,
        leagues.country_flag_url,
        leagues.season_api_year,
        leagues.season_start_date,
        leagues.season_end_date,
        leagues.season_is_current,
        leagues.has_coverage_fixture_events,
        leagues.has_coverage_fixture_lineups,
        leagues.has_coverage_fixture_statistics,
        leagues.has_coverage_fixture_players,
        leagues.has_coverage_standings,
        leagues.has_coverage_players,
        leagues.has_coverage_top_scorers,
        leagues.has_coverage_top_assists,
        leagues.has_coverage_top_cards,
        leagues.has_coverage_injuries,
        leagues.has_coverage_predictions,
        leagues.has_coverage_odds,
        leagues.raw_ingested_at,
        coalesce(overrides.country_name, leagues.country) as league_country
    from import_stg_apif__leagues as leagues
    left join import_country_name_overrides as overrides
        on leagues.country = overrides.provider_country
    where leagues.league_api_id is not null and leagues.season_api_year is not null
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
