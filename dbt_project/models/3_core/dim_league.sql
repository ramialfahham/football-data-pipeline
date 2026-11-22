with import_base_apif__league_entity as (
    select * from {{ ref('base_apif__league_entity') }}
),

import_competition_registry as (
    select * from {{ ref('competition_registry') }}
),

import_competition_types as (
    select * from {{ ref('competition_types') }}
),

import_base_apif__crest_objects as (
    select * from {{ ref('base_apif__crest_objects') }}
)

select
    cast(leagues.league_api_id as int64) as league_sk,
    leagues.league_code,
    leagues.league_api_id,
    leagues.league_name,
    leagues.league_type,
    leagues.league_country,
    leagues.country_flag_url,
    registry.competition_type,
    types.entity_type,
    registry.parent_competition,
    registry.confederation,
    registry.slug,
    registry.season_type,
    leagues.raw_ingested_at,
    case
        when crests.provider_id is not null
            then concat('/crests/leagues/', cast(leagues.league_api_id as string), '-104.webp')
    end as league_logo_url
from import_base_apif__league_entity as leagues
left join import_competition_registry as registry
    on leagues.league_code = registry.league_code
left join import_competition_types as types
    on registry.competition_type = types.competition_type
left join import_base_apif__crest_objects as crests
    on
        leagues.league_api_id = crests.provider_id
        and crests.crest_kind = 'leagues'
