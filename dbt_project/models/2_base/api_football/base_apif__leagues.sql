-- Unified league-season rows across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Output grain: (league_code, league_api_id, season_api_year).
{% set league_codes = var('active_competition_league_codes') %}

with src as (

    {% for lc in league_codes %}
    {% if not loop.first %}

    union all

    {% endif %}
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
    from {{ ref('stg_apif__' ~ lc | lower ~ '_leagues') }}
    where league_api_id is not null and season_api_year is not null

    {% endfor %}

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
