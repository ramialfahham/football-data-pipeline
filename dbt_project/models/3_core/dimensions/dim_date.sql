with historical_bounds as (
    select
        min(match_date) as min_date,
        max(match_date) as max_date
    from (
        select match_date from {{ ref('base_football_data__d1') }}
        union all
        select match_date from {{ ref('base_football_data__e0') }}
    )
),
calendar as (
    select day_date
    from historical_bounds,
    unnest(generate_date_array(min_date, date_add(max_date, interval 365 day), interval 1 day)) as day_date
)

select
    cast(format_date('%Y%m%d', day_date) as int64) as date_id,
    day_date as date_day,
    extract(year from day_date) as year_num,
    extract(month from day_date) as month_num,
    extract(day from day_date) as day_num,
    extract(week from day_date) as week_num,
    format_date('%A', day_date) as day_name,
    case when extract(dayofweek from day_date) in (1, 7) then true else false end as is_weekend
from calendar
