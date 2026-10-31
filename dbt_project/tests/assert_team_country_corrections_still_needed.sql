-- A country correction fills a country the provider does not send. Once the provider sends one,
-- the row is dead weight or a disagreement: either way someone must look, so it is reported.
--
-- Compares against base_apif__teams (PRE-correction), deduplicated exactly as
-- base_apif__teams_global does, so the comparison is against the row that model publishes.
{{ config(severity = 'warn', store_failures = true) }}

with import_base_apif__teams as (
    select * from {{ ref('base_apif__teams') }}
),

import_team_country_corrections as (
    select * from {{ ref('team_country_corrections') }}
),

provider_country as (
    select
        team_api_id,
        team_country
    from import_base_apif__teams
    qualify row_number() over (
        partition by team_api_id
        order by raw_ingested_at desc
    ) = 1
)

select
    corrections.team_api_id,
    corrections.team_country as corrected_country,
    provider.team_country as provider_country
from import_team_country_corrections as corrections
inner join provider_country as provider
    on corrections.team_api_id = provider.team_api_id
where nullif(trim(provider.team_country), '') is not null
