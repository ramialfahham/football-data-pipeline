-- A name override must still be a CORRECTION. If the provider has since adopted the same
-- name, the row is dead weight: it silently does nothing, and the next reader cannot tell
-- whether it is load-bearing or stale. Fail so it gets removed.
--
-- Compares against base_apif__teams (PRE-override) rather than base_apif__teams_global,
-- which is where the coalesce is applied and would therefore always agree with the seed.
-- The dedup below deliberately mirrors base_apif__teams_global's own
-- `qualify row_number() ... order by raw_ingested_at desc` so the comparison is against the
-- same provider row that model would have published.
--
-- warn: a dead row changes nothing a fan sees, so it is reported, not a reason to stop the build.
{{ config(severity = 'warn', store_failures = true) }}

with import_base_apif__teams as (
    select * from {{ ref('base_apif__teams') }}
),

import_team_name_overrides as (
    select * from {{ ref('team_name_overrides') }}
),

provider_name as (
    select
        team_api_id,
        team_name
    from import_base_apif__teams
    qualify row_number() over (
        partition by team_api_id
        order by raw_ingested_at desc
    ) = 1
)

select
    overrides.team_api_id,
    overrides.team_name as override_name,
    provider.team_name as provider_name
from import_team_name_overrides as overrides
inner join provider_name as provider
    on overrides.team_api_id = provider.team_api_id
where overrides.team_name = provider.team_name
