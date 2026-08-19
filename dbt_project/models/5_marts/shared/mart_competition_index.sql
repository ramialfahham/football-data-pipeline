{{ config(materialized='table') }}

{#
    One row per competition — the SINGLE source for the competitions page (#54, #62 step 3).
    Before this, that page would have read four things to render one row: the registry YAML,
    competition_types.csv, confederations.csv and dim_league. content_architecture.md §1 forbids
    that, and #62 is the fix.

    ORDERING. This mart carries the ordering INPUTS as facts and does not pre-bake the answer.
    The page spec declares the ORDER BY (CPO, 2026-08-16: sorting is arrangement, not a fact a
    visitor reads). The approved rule is:

        has an upcoming fixture       -- the 20 dormant competitions cannot compete on proximity
        days until next kickoff       -- BUCKETED BY CALENDAR DAY, not by timestamp
        region_rank                   -- the judgement, and the only hand-set input
        next_kickoff_datetime         -- deterministic tiebreak inside a day
        league_code                   -- full determinism

    and for competitions with nothing upcoming: last_kickoff_datetime descending, most recently
    played first. Bucketing by day is deliberate: the raw clock would rank the Eredivisie above
    the Premier League on a shared matchday for kicking off at 10:15 instead of 19:00.

    The registry's `sort_order` is deliberately ABSENT — declared obsolete by the CPO on
    2026-08-16. Its last consumer on the site was the home page's browse block, DROPPED
    2026-08-19; it now feeds only `build_nav()`/`nav.json`, an export target with no frontend
    consumer. Either way it is not this model's ordering basis, and this model does not remove it.

    LABELS. English name AND i18n key, never a translated string (#62, 2026-08-14).
    region_label_i18n_key is NULL when the region is a country, because a country name is an
    entity name rather than chrome.
#}

with import_competition_registry as (
    select * from {{ ref('competition_registry') }}
),

import_competition_types as (
    select * from {{ ref('competition_types') }}
),

import_confederations as (
    select * from {{ ref('confederations') }}
),

import_dim_league as (
    select * from {{ ref('dim_league') }}
),

import_fct_fixture as (
    select * from {{ ref('fct_fixture') }}
),

-- Kickoff proximity, per competition. Split rather than conditionally aggregated so each side
-- keeps its own grain: the next fixture ahead of now, and the last one behind it.
next_fixture as (
    select
        league_code,
        min(kickoff_datetime) as next_kickoff_datetime
    from import_fct_fixture
    where kickoff_datetime >= current_timestamp()
    group by league_code
),

last_fixture as (
    select
        league_code,
        max(kickoff_datetime) as last_kickoff_datetime
    from import_fct_fixture
    where kickoff_datetime < current_timestamp()
    group by league_code
),

-- A blank display_group means "not browsable" and the seed uses it deliberately for the three
-- friendly types (#54 note 3). Excluded here rather than given a heading. Today this removes
-- ZERO rows -- no registry competition carries a friendly type -- but the rule is the seed's,
-- not this model's, and encoding it here keeps the page correct the day one is onboarded.
browsable as (
    select
        registry.league_code,
        registry.competition_type,
        registry.slug,
        registry.confederation,
        types.entity_type,
        types.label_en as category_label_en,
        types.label_i18n_key as category_label_i18n_key
    from import_competition_registry as registry
    inner join import_competition_types as types
        on registry.competition_type = types.competition_type
    where
        types.display_group is not null
        and trim(types.display_group) != ''
)

select
    browsable.league_code,
    browsable.competition_type,
    browsable.entity_type,
    browsable.slug,
    browsable.category_label_en,
    browsable.category_label_i18n_key,
    browsable.confederation,
    confed.region_rank,
    leagues.league_name as competition_name,
    leagues.league_logo_url as logo_url,
    next_fixture.next_kickoff_datetime,
    last_fixture.last_kickoff_datetime,

    -- The region sub-line resolves HERE, so the page never sees the branch (#54 note 4).
    -- Which relationship is populated IS the answer (#69 step 5): league_country is NULL for
    -- every international/continental competition (the base layer turns the provider's 'World'
    -- sentinel into NULL, never a corrected string), so testing it directly replaces the
    -- competition_types.single_country flag the CPO rejected on 2026-08-16 -- there is no
    -- second taxonomy statement to keep in sync with the FK.
    coalesce(leagues.league_country, confed.label_en) as region_label_en,
    case
        when leagues.league_country is null then confed.label_i18n_key
    end as region_label_i18n_key
from browsable
left join import_confederations as confed
    on browsable.confederation = confed.confederation
left join import_dim_league as leagues
    on browsable.league_code = leagues.league_code
left join next_fixture
    on browsable.league_code = next_fixture.league_code
left join last_fixture
    on browsable.league_code = last_fixture.league_code
