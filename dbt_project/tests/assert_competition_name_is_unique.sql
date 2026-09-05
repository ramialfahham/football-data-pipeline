-- No two competitions may share a display name.
--
-- This is the defect the league_name_overrides seed exists for, asserted at the surface that
-- renders it. API-Football sends `Serie A` for BOTH Italy's SA and Brazil's BSA, and because
-- `mart_competition_index.competition_name` drives a competition page's <title>, <meta
-- description> and <h1>, two competitions shipped byte-identical SEO surfaces. The site's own
-- audit refuses that (audit-seo.mjs check 5, uniqueness within a locale), so it failed a build
-- rather than shipping — but only once a page existed to fail. This test catches it in the
-- warehouse, where it starts, and for every competition rather than only the ones a page is
-- built for today.
--
-- Asserted on the MART, not on dim_league, deliberately: the mart is what the export reads and
-- it applies the browsable filter, so this checks the set that actually reaches a reader. A
-- duplicate among non-browsable competitions is not a rendering defect.

with import_mart_competition_index as (
    select * from {{ ref('mart_competition_index') }}
)

select
    competition_name,
    count(*) as competitions_sharing_the_name,
    string_agg(league_code order by league_code) as league_codes
from import_mart_competition_index
where competition_name is not null
group by competition_name
having count(*) > 1
