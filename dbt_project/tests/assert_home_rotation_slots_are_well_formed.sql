-- The slots Home draws from hold three facts the draw depends on: a slot's weight is one number
-- repeated on each of its groups, the distinct slot weights add up to 100, and exactly one slot is
-- the fallback. Each broken fact returns a row.
{{ config(severity = 'error', store_failures = true) }}

with slots as (
    select * from {{ ref('home_rotation_slots') }}
),

weight_differs_within_a_slot as (
    select
        slot,
        'slot_weight differs between the rows of the slot' as problem
    from slots
    group by slot
    having count(distinct slot_weight) > 1
),

fallback_differs_within_a_slot as (
    select
        slot,
        'is_fallback_slot differs between the rows of the slot' as problem
    from slots
    group by slot
    having count(distinct is_fallback_slot) > 1
),

weights_do_not_add_up as (
    select
        cast(null as string) as slot,
        'the distinct slot weights do not add up to 100' as problem
    from (
        select sum(slot_weight) as total_weight
        from (
            select distinct
                slot,
                slot_weight
            from slots
        )
    )
    where total_weight != 100
),

not_exactly_one_fallback as (
    select
        cast(null as string) as slot,
        'there is not exactly one fallback slot' as problem
    from (
        select count(distinct if(is_fallback_slot, slot, null)) as fallback_slots
        from slots
    )
    where fallback_slots != 1
)

select * from weight_differs_within_a_slot
union all
select * from fallback_differs_within_a_slot
union all
select * from weights_do_not_add_up
union all
select * from not_exactly_one_fallback
