import uuid
from datetime import datetime, timezone

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

OPS_DATASET_ID = "OPS"
OPS_TABLE_ID = "INGESTION_RUNS"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_ops_table(client: bigquery.Client, project_id: str) -> str:
    table_id = f"{project_id}.{OPS_DATASET_ID}.{OPS_TABLE_ID}"
    try:
        client.get_table(table_id)
        return table_id
    except NotFound:
        pass

    dataset_ref = f"{project_id}.{OPS_DATASET_ID}"
    try:
        client.get_dataset(dataset_ref)
    except NotFound:
        client.create_dataset(bigquery.Dataset(dataset_ref), exists_ok=True)

    schema = [
        bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("started_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("ended_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("duration_seconds", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("tables_loaded", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("errors_count", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("error_sample", "STRING", mode="NULLABLE"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)
    return table_id


def init_run(pipeline_name: str) -> dict:
    return {
        "run_id": str(uuid.uuid4()),
        "pipeline_name": pipeline_name,
        "started_at": datetime.now(timezone.utc),
    }


def write_run_log(
    client: bigquery.Client,
    project_id: str,
    run_ctx: dict,
    status: str,
    tables_loaded: int,
    errors_count: int,
    error_sample: str = "",
) -> None:
    table_id = ensure_ops_table(client, project_id)
    ended_at = datetime.now(timezone.utc)
    duration_seconds = (ended_at - run_ctx["started_at"]).total_seconds()

    rows = [
        {
            "run_id": run_ctx["run_id"],
            "pipeline_name": run_ctx["pipeline_name"],
            "status": status,
            "started_at": run_ctx["started_at"].isoformat(),
            "ended_at": ended_at.isoformat(),
            "duration_seconds": duration_seconds,
            "tables_loaded": tables_loaded,
            "errors_count": errors_count,
            "error_sample": (error_sample or "")[:1000],
        }
    ]
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"Failed writing ingestion run log: {errors}")
