{#
  Every researched line-up in fixture_lineup_corrections is applied and holds. Returns one row
  per broken match:
  - not_applied: the match has seed rows but no researched rows in base_apif__lineups;
  - fails_check: base_apif__lineups finds it failing a line-up check other than the squad lists,
    which an official source outranks;
  - source_not_valid: a source that is not https, or match reports from fewer than two sites.
#}
{{ config(store_failures = true, severity = 'error') }}

with seeded_rows as (
    select
        fixture_id,
        source_kind,
        source as source_urls
    from {{ ref('fixture_lineup_corrections') }}
),

seeded as (
    select distinct fixture_id
    from seeded_rows
),

applied as (
    select
        lineups.fixture_id,
        logical_and(lineups.lineup_state = 'researched') as is_researched,
        any_value(lineups.failed_checks) as failed_checks
    from {{ ref('base_apif__lineups') }} as lineups
    inner join seeded
        on lineups.fixture_id = seeded.fixture_id
    group by lineups.fixture_id
),

sources as (
    select
        seeded_rows.fixture_id,
        seeded_rows.source_kind,
        seeded_rows.source_urls,
        countif(not starts_with(url, 'https://')) as n_not_https,
        count(distinct net.host(url)) as n_sites
    from seeded_rows,
        unnest(split(seeded_rows.source_urls, ' ')) as url
    where url != ''
    group by seeded_rows.fixture_id, seeded_rows.source_kind, seeded_rows.source_urls
),

failing as (
    select distinct applied.fixture_id
    from applied,
        unnest(applied.failed_checks) as failed_check
    where failed_check != 'squad_lists'
)

select
    seeded.fixture_id,
    'not_applied' as problem
from seeded
left join applied
    on seeded.fixture_id = applied.fixture_id
where not coalesce(applied.is_researched, false)

union all

select
    fixture_id,
    'fails_check' as problem
from failing

union all

select
    sources.fixture_id,
    'source_not_valid' as problem
from sources
where
    sources.n_not_https > 0
    or (sources.source_kind = 'match_reports' and sources.n_sites < 2)
