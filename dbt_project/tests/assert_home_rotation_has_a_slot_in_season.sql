-- The data-quality alert of Home's group rotation: Home draws a slot among those in season, and
-- when none is, it shows the fallback slot's last completed season instead of an empty block. That
-- keeps the page up and hides the cause, which is an ingest gap, so this test fails the build and
-- the nightly's failure alert fires. It returns one row when no 'current' row is in season.
{{ config(severity = 'error', store_failures = true) }}

select 'no slot of Home is in season' as problem
from (
    select count(*) as leagues_in_season
    from {{ ref('mart_home_rotation') }}
    where board_role = 'current' and is_in_season
)
where leagues_in_season = 0
