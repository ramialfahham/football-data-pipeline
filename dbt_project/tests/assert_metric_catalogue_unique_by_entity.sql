-- The catalogue grain is (metric_id, entity): the same metric family may exist
-- for team and player (e.g. duels_won_pct). A plain unique test
-- on metric_id is wrong at this grain and was failing; this enforces the real key.
select
    metric_id,
    entity,
    count(*) as n
from {{ ref('metric_catalogue') }}
group by metric_id, entity
having count(*) > 1
