-- A country name override must still be a CORRECTION. Two ways a row stops being one, and
-- both mean "delete it" rather than "leave it and hope":
--
--   1. The override equals the provider's own string. It silently does nothing, and the next
--      reader cannot tell whether it is load-bearing or dead weight.
--   2. The provider string no longer appears at all -- because the provider fixed its own
--      spelling, or because the only competition that carried it was offboarded. The row then
--      matches nothing and the seed slowly fills with fiction.
--
-- ⚠ WIDENED FOR #69. The first version compared against stg_apif__leagues ALONE, because the
-- seed was leagues-only (3 rows). The seed now maps strings from all four provider surfaces, and
-- `stg_apif__leagues.country` holds just 19 distinct values -- so a leagues-only comparison would
-- report 64 of the 67 rows as dead when they are real corrections for team, player and coach
-- values. Narrowed to where the assertion still holds, rather than downgraded: every row must
-- still match a string the provider actually sends SOMEWHERE.
--
-- Compares against STAGING (pre-override) rather than base or core, which is where the coalesce
-- is applied and would therefore always agree with the seed.
--
-- warn: a dead row changes nothing a fan sees, so it is reported, not a reason to stop the build.
{{ config(severity = 'warn', store_failures = true) }}

with import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

provider_countries as (
    select country
    from {{ ref('stg_apif__leagues') }}
    where country is not null

    union distinct

    select team_country
    from {{ ref('stg_apif__teams') }}
    where team_country is not null

    union distinct

    select coach_birth_country
    from {{ ref('stg_apif__coaches') }}
    where coach_birth_country is not null

    union distinct

    select birth_country
    from {{ ref('stg_apif__player_profiles') }}
    where birth_country is not null
)

select
    overrides.provider_country,
    overrides.country_name as override_name,
    provider.country as provider_country_seen
from import_country_name_overrides as overrides
left join provider_countries as provider
    on overrides.provider_country = provider.country
where
    provider.country is null
    or overrides.provider_country = overrides.country_name
