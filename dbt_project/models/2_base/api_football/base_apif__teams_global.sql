-- Global team entity: one row per team_api_id (latest ingest across league_code rows).
-- Feeds dim_team. Grain: team_api_id.
--
-- Applies the CPO-owned name corrections here rather than in dim_team so the core
-- dimension publishes an entity that is already settled (CPO ruling, 2026-07-27: base is
-- where these preparations happen, the dim propagates the result). Why it matters beyond
-- spelling: the provider's /teams endpoint sends a short label of unverified quality
-- ("Rangers", "Lokomotiv"), and it is the ONLY team name in the product -- it drives the
-- fixture card, the page H1, the <title>, the meta description and the URL slug, so 18
-- teams in 9 groups were previously indistinguishable from one another (#850, #851).

with import_base_apif__teams as (
    select * from {{ ref('base_apif__teams') }}
),

import_team_name_overrides as (
    select * from {{ ref('team_name_overrides') }}
),

latest_per_team as (
    select *
    from import_base_apif__teams
    qualify row_number() over (
        partition by team_api_id
        order by raw_ingested_at desc
    ) = 1
)

-- Columns are enumerated rather than passed through with a wildcard: adding the override
-- join makes `select teams.* replace (...)` ambiguous to SQLFluff (AM04, "unknown number of
-- result columns"), and this repo suppresses no lint rule anywhere -- there is not a single
-- `noqa` in it. Nothing is lost by listing them: dim_team is the only consumer and already
-- projects its columns explicitly, so a new upstream column needs an edit there regardless.
select
    teams.league_code,
    teams.team_api_id,
    teams.team_code,
    teams.team_country,
    teams.team_founded_year,
    teams.team_logo_url,
    teams.venue_api_id,
    teams.venue_name,
    teams.venue_address,
    teams.venue_city,
    teams.venue_capacity,
    teams.raw_ingested_at,
    coalesce(overrides.team_name, teams.team_name) as team_name
from latest_per_team as teams
left join import_team_name_overrides as overrides
    on teams.team_api_id = overrides.team_api_id
