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

## Observability

Use **Cloud Logging** (function stdout/stderr and request logs) and **Cloud Scheduler** job history to confirm runs and debug failures. There is no separate BigQuery ops dataset for run metadata.

## Error Handling

- Use request timeouts.
- Continue per table when safe and record partial failures.
- Return HTTP 500 only for fatal run-level failures.

For **API-Football**, treat provider responses as documented: inspect JSON `errors` and `paging` even on HTTP 200, merge all pages where the API paginates, and avoid hammering the API (single retry on 429 / 5xx with backoff, optional pacing between calls). See [`docs/data_contract.md`](data_contract.md) and the [API-Football beginner’s guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide).

## Suggested Schedules (prototype)

- `api_football`: several times daily (see `docs/data_contract.md`).
