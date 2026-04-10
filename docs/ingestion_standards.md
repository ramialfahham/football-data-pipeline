# Ingestion Operations Standards

This project runs ingestion without Airflow. The standard operating pattern is:

1. Cloud Scheduler triggers ingestion functions.
2. Ingestion writes raw data to BigQuery datasets.
3. dbt runs afterward to validate and model data.

## Pipeline Contract

Each ingestion pipeline should provide:

- clear entrypoint function
- source configuration via environment variables
- deterministic table naming
- idempotent write strategy per table (`WRITE_TRUNCATE` for snapshots)

## Run Logging

All ingestion pipelines must write a run log row to:

- dataset: `OPS`
- table: `INGESTION_RUNS`

Fields:

- `run_id`
- `pipeline_name`
- `status` (`success`, `partial_success`, `failed`)
- `started_at`, `ended_at`, `duration_seconds`
- `tables_loaded`
- `errors_count`
- `error_sample`

## Error Handling

- Use request timeouts.
- Continue per table when safe and record partial failures.
- Return HTTP 500 only for fatal run-level failures.
- Always attempt to write run logs.

## Suggested Schedules (prototype)

- `football_data_co_uk`: daily

## Minimal Monitoring Queries

Run health over last 7 days:

```sql
select
  pipeline_name,
  status,
  count(*) as runs
from `football-data-pipeline-gcp.OPS.INGESTION_RUNS`
where started_at >= timestamp_sub(current_timestamp(), interval 7 day)
group by 1, 2
order by 1, 2;
```
