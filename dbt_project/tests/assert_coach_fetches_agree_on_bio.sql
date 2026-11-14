{#
  The fetches of one coach never give two different values for a bio field. Returns one row per coach
  and field with more than one value in stg_apif__coaches; there, the newest value stands.
#}
{{ config(store_failures = true, severity = 'warn') }}

with values_per_coach as (
    select
        coach_id,
        count(distinct coach_name) as coach_name,
        count(distinct coach_first_name) as coach_first_name,
        count(distinct coach_last_name) as coach_last_name,
        count(distinct coach_birth_date) as coach_birth_date,
        count(distinct coach_birth_place) as coach_birth_place,
        count(distinct coach_birth_country) as coach_birth_country,
        count(distinct coach_nationality) as coach_nationality
    from {{ ref('stg_apif__coaches') }}
    where coach_id is not null
    group by coach_id
)

select
    values_per_coach.coach_id,
    field.field_name,
    field.value_count
from values_per_coach
cross join
    unnest([
        struct('coach_name' as field_name, values_per_coach.coach_name as value_count),
        struct('coach_first_name', values_per_coach.coach_first_name),
        struct('coach_last_name', values_per_coach.coach_last_name),
        struct('coach_birth_date', values_per_coach.coach_birth_date),
        struct('coach_birth_place', values_per_coach.coach_birth_place),
        struct('coach_birth_country', values_per_coach.coach_birth_country),
        struct('coach_nationality', values_per_coach.coach_nationality)
    ]) as field
where field.value_count > 1
