with runs as (
    select
        pipeline_name,
        status,
        started_at,
        ended_at,
        duration_seconds,
        tables_loaded,
        errors_count,
        error_sample
    from `{{ target.project }}.OPS.INGESTION_RUNS`
),
last_7_days as (
    select *
    from runs
    where started_at >= timestamp_sub(current_timestamp(), interval 7 day)
),
latest_failed as (
    select
        pipeline_name,
        ended_at as last_failed_at,
        error_sample as last_error_sample,
        row_number() over (partition by pipeline_name order by ended_at desc) as rn
    from runs
    where status in ('failed', 'partial_success')
),
agg as (
    select
        pipeline_name,
        count(*) as runs_7d,
        countif(status = 'success') as success_runs_7d,
        safe_divide(countif(status = 'success'), count(*)) as success_rate_7d,
        avg(duration_seconds) as avg_duration_seconds_7d,
        max(ended_at) as last_run_at,
        sum(tables_loaded) as tables_loaded_7d,
        sum(errors_count) as errors_7d
    from last_7_days
    group by pipeline_name
)

select
    a.pipeline_name,
    a.runs_7d,
    a.success_runs_7d,
    a.success_rate_7d,
    a.avg_duration_seconds_7d,
    a.last_run_at,
    a.tables_loaded_7d,
    a.errors_7d,
    f.last_failed_at,
    f.last_error_sample
from agg a
left join latest_failed f
    on a.pipeline_name = f.pipeline_name
   and f.rn = 1
