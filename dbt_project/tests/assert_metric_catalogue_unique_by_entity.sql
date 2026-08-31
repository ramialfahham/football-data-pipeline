-- The catalogue grain is (metric_id, entity): the same metric family may exist
-- for team and player under one id. A plain unique test on metric_id is wrong at
-- this grain and was failing; this enforces the real key. No instance is named
-- here on purpose — step 4 of the naming programme renames every player id that
-- currently collides, so a quoted example would date.
select
    metric_id,
    entity,
    count(*) as n
from {{ ref('metric_catalogue') }}
group by metric_id, entity
having count(*) > 1
