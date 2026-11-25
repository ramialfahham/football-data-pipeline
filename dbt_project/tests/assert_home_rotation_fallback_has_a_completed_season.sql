-- The fallback shows the fallback slot's last completed season, so that slot must have a
-- 'fallback' row, or the fallback itself would be the empty block it exists to prevent.
{{ config(severity = 'error', store_failures = true) }}

select 'the fallback slot has no completed season' as problem
from (
    select count(*) as fallback_leagues
    from {{ ref('mart_home_rotation') }}
    where board_role = 'fallback' and is_fallback_slot
)
where fallback_leagues = 0
