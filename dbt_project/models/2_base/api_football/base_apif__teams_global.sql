-- Global team entity: one row per team_api_id (latest ingest across league_code rows).
-- Feeds dim_team. Grain: team_api_id.
--
-- Applies the hand-curated name corrections here rather than in dim_team so the core
-- dimension publishes an entity that is already settled: base is where these preparations
-- happen, the dim propagates the result. Why it matters beyond
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

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

latest_per_team as (
    select *
    from import_base_apif__teams
    qualify row_number() over (
        partition by team_api_id
        order by raw_ingested_at desc
    ) = 1
),

-- Columns are enumerated rather than passed through with a wildcard: the override join makes
-- `select teams.* replace (...)` ambiguous to SQLFluff (AM04, "unknown number of result
-- columns"), and this repo suppresses no lint rule anywhere -- there is not a single `noqa`
-- in it. Nothing is lost by listing them: dim_team is the only consumer and already projects
-- its columns explicitly, so a new upstream column needs an edit there regardless.
-- team_country_raw is kept alongside the corrected team_country and flows through the slug CTEs
-- below unexported (the terminal select is an explicit column list, not a wildcard, so it never
-- reaches dim_team). The slug ladder anchors on team_country_raw, not the corrected value:
-- kebab_slug already normalises the team-surface hyphenation defect to the same anchor either
-- way, but a handful of overrides are semantic renames (USA -> United States of America, Congo-DR
-- -> DR Congo), and #852's slugs are assigned once and never re-derived -- anchoring on the
-- corrected value would silently reshuffle any contested team's slug the day its country's
-- canonical spelling changes, which is exactly what that guard exists to prevent.
corrected as (
    select
        teams.league_code,
        teams.team_api_id,
        teams.team_code,
        teams.team_country as team_country_raw,
        teams.team_founded_year,
        teams.team_logo_url,
        teams.venue_api_id,
        teams.venue_name,
        teams.venue_address,
        teams.venue_city,
        teams.venue_capacity,
        teams.raw_ingested_at,
        coalesce(overrides.team_name, teams.team_name) as team_name,
        coalesce(country_overrides.country_name, teams.team_country) as team_country
    from latest_per_team as teams
    left join import_team_name_overrides as overrides
        on teams.team_api_id = overrides.team_api_id
    left join import_country_name_overrides as country_overrides
        on teams.team_country = country_overrides.provider_country
),

-- team_slug: the permanent, locale-independent team URL (#852). Derived HERE and not in the
-- export, because assigning an identifier is derivation and the export is the consumption
-- layer (#846). Derived AFTER the name is settled above -- a slug built from an uncorrected
-- provider name would be the wrong URL.
--
-- The ladder is SYMMETRIC: a contested name is given to NOBODY, so no ranking, no importance
-- ordering and no per-collision adjudication is ever needed.
--
-- Each candidate is also tested against the strings already assigned, not merely against its own
-- contending group. Two hazards need that, both LATENT on today's data rather than firing:
--   * a level-2 candidate equalling a DIFFERENT team's level-1 slug. `Ararat` + Armenia would
--     yield `ararat-armenia`, which is `Ararat-Armenia`'s own bare slug. Both sit at level 1
--     today because `ararat` is uncontested, so the anti-join has never fired -- one more
--     Armenian club named Ararat is all it takes.
--   * a level-3 `{name}-{id}` equalling an existing bare slug, since club names embed digits
--     (`1899 Hoffenheim` owns `hoffenheim-1899`).
-- Both are caught here rather than by the `unique` test on dim_team.team_slug, because the
-- nightly runs a bare `dbt build` and a failed test there skips every downstream model. What is
-- deliberately NOT caught here is the residual beyond level 3 -- see the terminal's comment.
--
-- A team that won its bare slug at level 1 KEEPS it; only the escalating team falls through.
-- Penalising the bystander would be the wrong reading of "symmetric".
--
-- Three CTE steps rather than one expression: the whole slug pipeline nested in a single
-- expression exceeds SQLFluff's parse-depth limit once the templater expands it. The probed
-- ceiling is about eight nested function calls (see the macro's note).
prepared as (
    select
        corrected.*,
        {{ slug_prepare('team_name') }} as name_prepared,
        {{ slug_prepare('team_country_raw') }} as country_prepared
    from corrected
),

transliterated as (
    select
        prepared.*,
        {{ translit_latin('name_prepared') }} as name_ascii,
        {{ translit_latin('country_prepared') }} as country_ascii
    from prepared
),

candidates as (
    select
        transliterated.*,
        {{ kebab_slug('name_ascii') }} as slug_base,
        {{ kebab_slug('country_ascii') }} as slug_anchor
    from transliterated
),

base_contended as (
    select
        candidates.*,
        count(*) over (partition by slug_base) as base_contenders
    from candidates
),

-- level 1 winners: their slug is settled and must not be taken by anyone escalating
accepted_level_1 as (
    select distinct slug_base as taken
    from base_contended
    where
        base_contenders = 1
        and slug_base != ''
),

anchored as (
    select
        base_contended.*,
        case
            when base_contenders > 1 and slug_anchor != ''
                then concat(slug_base, '-', slug_anchor)
        end as slug_anchored
    from base_contended
),

anchor_contended as (
    select
        anchored.*,
        accepted_level_1.taken is not null as anchor_hits_level_1,
        countif(anchored.base_contenders > 1)
            over (partition by anchored.slug_anchored) as anchor_contenders
    from anchored
    left join accepted_level_1
        on anchored.slug_anchored = accepted_level_1.taken
),

-- every string already taken by the time level 3 runs. Level 3 must be tested against THIS,
-- not merely against its own peers: `{name}-{id}` is unique among id-suffixed rows because the
-- id is, but nothing stops it equalling a level-1 winner's bare slug. Club names embed digits
-- routinely (1899 Hoffenheim, 1860 Munchen, 1. FC Koln), so a bare slug can end in `-NNNN`.
assigned_before_level_3 as (
    select distinct slug_base as taken
    from anchor_contended
    where
        base_contenders = 1
        and slug_base != ''
    union distinct
    select distinct slug_anchored
    from anchor_contended
    where
        slug_anchored is not null
        and not anchor_hits_level_1
        and anchor_contenders = 1
),

level_3 as (
    select
        anchor_contended.*,
        concat(
            coalesce(nullif(slug_anchored, ''), nullif(slug_base, ''), 'team'),
            '-',
            cast(team_api_id as string)
        ) as slug_with_id
    from anchor_contended
),

level_3_checked as (
    select
        level_3.*,
        assigned_before_level_3.taken is not null as id_slug_taken
    from level_3
    left join assigned_before_level_3
        on level_3.slug_with_id = assigned_before_level_3.taken
)

select
    league_code,
    team_api_id,
    team_code,
    team_country,
    team_founded_year,
    team_logo_url,
    venue_api_id,
    venue_name,
    venue_address,
    venue_city,
    venue_capacity,
    raw_ingested_at,
    team_name,
    case
        -- level 1: an uncontested name takes its own slug
        when base_contenders = 1 and slug_base != '' then slug_base
        -- level 2: every contender takes the country anchor, if that is free everywhere
        when
            slug_anchored is not null
            and not anchor_hits_level_1
            and anchor_contenders = 1
            then slug_anchored
        -- level 3, terminal: the ONLY place a provider id appears in a URL. Fires for a
        -- same-country duplicate, a null country, or a name that folds to nothing -- and note
        -- that the first two of those are DATA DEFECTS (#850's open alias decision, and #853's
        -- 39 null countries of which 22 have a country sitting in stg_apif__teams), not naming
        -- problems. Fix those and this branch mostly stops firing.
        --
        -- If even this collides with an already-assigned slug, the row gets NULL and the
        -- not_null test on dim_team.team_slug stops the build and names the team. That is the
        -- CORRECT failure: it takes a club literally named "<X> <some other club's provider id>"
        -- in the same country as that club, which is a data situation a human should look at,
        -- not one an automatic escape hatch should paper over with a stranger URL.
        --
        -- An earlier revision invented a doubled-hyphen terminal here, on the grounds that
        -- kebab_slug can never emit `--` so it was provably unique. It was provably unique and it
        -- was a hack: it bought closure with a URL (`hoffenheim--1899`) that no reader should be
        -- shown, to avoid a case that fires zero times. Removed deliberately -- see the residual
        -- stated in base.yml rather than an escape hatch hidden in a case expression.
        when not id_slug_taken then slug_with_id
    end as team_slug
from level_3_checked
