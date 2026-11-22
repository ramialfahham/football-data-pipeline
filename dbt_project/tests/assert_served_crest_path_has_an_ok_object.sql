{#
  A team or league publishes a crest path only when its files are stored, and publishes the path
  that names its own id. Each failing row is a path with no stored object behind it, or a path
  that belongs to another id.
#}
{{ config(store_failures = true, severity = 'error') }}

with teams as (
    select
        'teams' as crest_kind,
        team_api_id as provider_id,
        team_logo_url as logo_path
    from {{ ref('dim_team') }}
    where team_logo_url is not null
),

leagues as (
    select
        'leagues' as crest_kind,
        league_api_id as provider_id,
        league_logo_url as logo_path
    from {{ ref('dim_league') }}
    where league_logo_url is not null
),

published as (
    select * from teams
    union all
    select * from leagues
),

stored as (
    select
        crest_kind,
        provider_id
    from {{ ref('base_apif__crest_objects') }}
),

expected as (
    select
        published.crest_kind,
        published.provider_id,
        published.logo_path,
        stored.provider_id as stored_provider_id,
        concat(
            '/crests/', published.crest_kind, '/', cast(published.provider_id as string), '-104.webp'
        ) as expected_path
    from published
    left join stored
        on
            published.crest_kind = stored.crest_kind
            and published.provider_id = stored.provider_id
)

select
    crest_kind,
    provider_id,
    logo_path
from expected
where
    stored_provider_id is null
    or logo_path != expected_path
