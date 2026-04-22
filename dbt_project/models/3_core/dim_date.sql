{{ config(materialized='table') }}

with date_series as (
    {{
        dbt_utils.date_spine(
            datepart="day",
            start_date="cast('1900-01-01' as date)",
            end_date="cast('2101-01-01' as date)"
        )
    }}
),

final as (
    select
        cast(format_date('%Y%m%d', date_day) as int64) as date_sk,
        date_day,
        extract(year from date_day) as calendar_year,
        extract(quarter from date_day) as calendar_quarter,
        extract(month from date_day) as calendar_month,
        format_date('%B', date_day) as calendar_month_name,
        extract(isoyear from date_day) as iso_year,
        extract(isoweek from date_day) as iso_week,
        extract(day from date_day) as day_of_month,
        extract(dayofweek from date_day) as day_of_week,
        format_date('%A', date_day) as day_of_week_name,
        extract(dayofweek from date_day) in (1, 7) as is_weekend
    from date_series
)

select * from final
