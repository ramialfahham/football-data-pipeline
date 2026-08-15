-- A country name override must still be a CORRECTION. Two ways a row stops being one, and
-- both mean "delete it" rather than "leave it and hope":
--
--   1. The override equals the provider's own string. It silently does nothing, and the next
--      reader cannot tell whether it is load-bearing or dead weight.
--   2. The provider string no longer appears at all -- because the provider fixed its own
--      spelling, or because the only competition that carried it was offboarded. The row then
--      matches nothing and the seed slowly fills with fiction.
--
-- Compares against stg_apif__leagues (PRE-override) rather than base_apif__leagues, which is
-- where the coalesce is applied and would therefore always agree with the seed.

with import_stg_apif__leagues as (
    select * from {{ ref('stg_apif__leagues') }}
),

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

provider_countries as (
    select distinct country
    from import_stg_apif__leagues
    where country is not null
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
