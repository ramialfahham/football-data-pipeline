-- A competition name override must still be a CORRECTION, and must still address a real
-- competition. Two ways a row goes bad, and both are silent without this test:
--   STALE    — the provider has since adopted the same name, so the row does nothing and the
--              next reader cannot tell whether it is load-bearing.
--   ORPHAN   — the league_code matches no ingested competition (a typo, or a competition that
--              left the registry), so the correction never applies to anything.
-- The team seed's equivalent, `assert_team_name_overrides_still_needed`, catches only the first,
-- because it joins INNER; this one reports both and names which in `reason`. (Its filename
-- follows this task's contract rather than that sibling's `_still_needed` convention.)
--
-- Compares against stg_apif__leagues (PRE-override) rather than base_apif__leagues, which is
-- where the coalesce is applied and would therefore always agree with the seed.
-- The dedup mirrors what base_apif__league_entity publishes — latest season, then latest
-- ingest — so the comparison is against the provider row that actually reaches dim_league.

with import_stg_apif__leagues as (
    select * from {{ ref('stg_apif__leagues') }}
),

import_league_name_overrides as (
    select * from {{ ref('league_name_overrides') }}
),

provider_name as (
    select
        league_code,
        league_name
    from import_stg_apif__leagues
    where league_code is not null
    qualify row_number() over (
        partition by league_code
        order by season_api_year desc, raw_ingested_at desc
    ) = 1
)

select
    overrides.league_code,
    overrides.league_name as override_name,
    provider.league_name as provider_name,
    case
        when provider.league_code is null
            then 'ORPHAN: league_code matches no ingested competition'
        else 'STALE: the provider now sends this exact name, so the row corrects nothing'
    end as reason
from import_league_name_overrides as overrides
left join provider_name as provider
    on overrides.league_code = provider.league_code
where
    provider.league_code is null
    or overrides.league_name = provider.league_name
