with import_base_apif__competition_seasons as (
    select * from {{ ref('base_apif__competition_seasons') }}
),

import_dim_league as (
    select * from {{ ref('dim_league') }}
),

import_competition_season_map as (
    select * from {{ ref('competition_season_map') }}
),

labelled as (
    select
        seasons.*,
        map.season_type,
        map.split_year_season,
        map.calendar_year_season,
        map.tier as map_tier,
        map.competition_group as map_competition_group,
        if(
            map.previous_season_api_year is null,
            null,
            {{ dbt_utils.generate_surrogate_key(['seasons.league_api_id', 'map.previous_season_api_year']) }}
        ) as previous_season_sk,
        case leagues.season_type
            when 'split_year'
                then concat(
                    cast(seasons.season_api_year as string),
                    '/',
                    lpad(cast(mod(seasons.season_api_year + 1, 100) as string), 2, '0')
                )
            when 'calendar_year' then cast(seasons.season_api_year as string)
        end as season_label
    from import_base_apif__competition_seasons as seasons
    left join import_dim_league as leagues
        on seasons.league_code = leagues.league_code
    left join import_competition_season_map as map
        on seasons.league_code = map.league_code and seasons.season_api_year = map.season_api_year
)

select
    {{ dbt_utils.generate_surrogate_key(['league_api_id', 'season_api_year']) }} as season_sk,
    cast(league_api_id as int64) as league_sk,
    league_code,
    league_api_id,
    season_api_year,
    season_label,
    season_type,
    split_year_season,
    calendar_year_season,
    -- A season the map leaves blank keeps the competition's latest earlier value.
    last_value(map_tier ignore nulls) over (
        partition by league_code order by season_api_year
        rows between unbounded preceding and current row
    ) as tier,
    last_value(map_competition_group ignore nulls) over (
        partition by league_code order by season_api_year
        rows between unbounded preceding and current row
    ) as competition_group,
    previous_season_sk,
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
