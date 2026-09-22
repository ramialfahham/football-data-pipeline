{#
  A metric group has exactly one order, and the orders are the positions 1..N (metric layer).
  `metric_group_order` is the one place the order of the groups is defined, and every surface
  renders groups in it. A group carrying two orders, two groups sharing one, or a gap in the
  sequence is a wrong page: a heading in the wrong place, or two groups fighting for a slot.
  The test FAILS (returns rows) for any group whose order breaks one of those three rules.

  Reads the seed in the target it runs in; on a merge request that is the branch's seed.
#}

{{ config(store_failures = true) }}

with per_group as (
    select
        metric_group,
        count(distinct metric_group_order) as orders_in_group,
        min(metric_group_order) as group_order
    from {{ ref('metric_catalogue') }}
    group by metric_group
),

positions as (
    select
        count(*) as group_count,
        count(distinct group_order) as distinct_orders,
        min(group_order) as first_order,
        max(group_order) as last_order
    from per_group
)

select
    g.metric_group,
    g.orders_in_group,
    g.group_order,
    p.group_count,
    p.distinct_orders,
    p.first_order,
    p.last_order
from per_group as g
cross join positions as p
where
    g.orders_in_group <> 1
    or p.distinct_orders <> p.group_count
    or p.first_order <> 1
    or p.last_order <> p.group_count
