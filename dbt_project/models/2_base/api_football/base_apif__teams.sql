-- Unified teams across all onboarded competitions (explicit ref() list).
-- Same algorithm as BL1: /teams endpoint plus fixture-derived team keys and name fallback.
-- Output grain: (league_code, team_api_id).

with stg_teams as (
    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__bl1_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wc_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wcqeu_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wcqaf_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wcqca_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wcqsa_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wcqas_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wcqip_teams') }}
    where team_id is not null

    union all

    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__wcqoc_teams') }}
    where team_id is not null
),

stg_fixtures as (
    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__bl1_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wc_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wcqeu_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wcqaf_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wcqca_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wcqsa_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wcqas_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wcqip_fixtures_next') }}

    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__wcqoc_fixtures_next') }}
),

team_keys as (
    select
        league_code,
        team_api_id
    from stg_teams

    union all

    select
        league_code,
        home_team_id as team_api_id
    from stg_fixtures
    where home_team_id is not null

    union all

    select
        league_code,
        away_team_id as team_api_id
    from stg_fixtures
    where away_team_id is not null
),

distinct_team_keys as (
    select distinct
        league_code,
        team_api_id
    from team_keys
),

teams_latest as (
    select
        *,
        row_number() over (
            partition by league_code, team_api_id
            order by season desc, raw_ingested_at desc
        ) as rn
    from stg_teams
),

fixture_team_names as (
    select
        league_code,
        team_api_id,
        team_name,
        raw_ingested_at,
        row_number() over (
            partition by league_code, team_api_id
            order by raw_ingested_at desc, fixture_id desc
        ) as rn
    from (
        select
            league_code,
            fixture_id,
            home_team_id as team_api_id,
            home_team_name as team_name,
            raw_ingested_at
        from stg_fixtures
        where home_team_id is not null and home_team_name is not null

        union all

        select
            league_code,
            fixture_id,
            away_team_id as team_api_id,
            away_team_name as team_name,
            raw_ingested_at
        from stg_fixtures
        where away_team_id is not null and away_team_name is not null
    )
)

select
    k.league_code,
    k.team_api_id,
    t.team_code,
    t.team_country,
    t.team_founded_year,
    t.team_logo_url,
    t.venue_api_id,
    t.venue_name,
    t.venue_address,
    t.venue_city,
    t.venue_capacity,
    coalesce(t.team_name, fn.team_name) as team_name,
    coalesce(t.raw_ingested_at, fn.raw_ingested_at) as raw_ingested_at
from distinct_team_keys as k
left join teams_latest as t
    on
        k.league_code = t.league_code
        and k.team_api_id = t.team_api_id
        and t.rn = 1
left join fixture_team_names as fn
    on
        k.league_code = fn.league_code
        and k.team_api_id = fn.team_api_id
        and fn.rn = 1
