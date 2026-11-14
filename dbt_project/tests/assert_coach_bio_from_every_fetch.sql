{#
  A coach's bio is the newest value any fetch carried. Returns one row per coach and bio field blank
  in base_apif__coaches while a fetch in stg_apif__coaches has it.
#}
{{ config(store_failures = true, severity = 'error') }}

with carried as (
    select
        coach_id,
        logical_or(coach_first_name is not null) as has_first_name,
        logical_or(coach_last_name is not null) as has_last_name,
        logical_or(coach_birth_date is not null) as has_birth_date,
        logical_or(coach_birth_place is not null) as has_birth_place,
        logical_or(coach_birth_country is not null) as has_birth_country,
        logical_or(coach_nationality is not null) as has_nationality
    from {{ ref('stg_apif__coaches') }}
    where coach_id is not null
    group by coach_id
)

select
    coach.coach_api_id,
    field.field_name
from {{ ref('base_apif__coaches') }} as coach
inner join carried
    on coach.coach_api_id = carried.coach_id
cross join
    unnest([
        struct('coach_first_name' as field_name, carried.has_first_name and coach.coach_first_name is null as lost),
        struct('coach_last_name', carried.has_last_name and coach.coach_last_name is null),
        struct('coach_birth_date', carried.has_birth_date and coach.coach_birth_date is null),
        struct('coach_birth_place', carried.has_birth_place and coach.coach_birth_place is null),
        struct('coach_birth_country', carried.has_birth_country and coach.coach_birth_country is null),
        struct('coach_nationality', carried.has_nationality and coach.coach_nationality is null)
    ]) as field
where field.lost
