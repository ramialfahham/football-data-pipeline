with import_base_apif__competition_seasons as (
    select * from {{ ref('base_apif__competition_seasons') }}
),

import_competition_registry as (
    select * from {{ ref('competition_registry') }}
),

labelled as (
    select
        seasons.*,
        case registry.season_type
            when 'split_year'
                then concat(
                    cast(seasons.season_api_year as string),
                    '/',
                    lpad(cast(mod(seasons.season_api_year + 1, 100) as string), 2, '0')
                )
            when 'calendar_year' then cast(seasons.season_api_year as string)
        end as season_label
    from import_base_apif__competition_seasons as seasons
    left join import_competition_registry as registry
        on seasons.league_code = registry.league_code
)

select
    {{ dbt_utils.generate_surrogate_key(['league_api_id', 'season_api_year']) }} as season_sk,
    cast(league_api_id as int64) as league_sk,
    league_code,
    league_api_id,
    season_api_year,
    season_label,
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
from labelled
