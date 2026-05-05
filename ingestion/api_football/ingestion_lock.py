"""Single-flight ingestion using a BigQuery lease row.

Overlaps are **reduced** (stale schedules, slow runs): a second job sees ``409`` while the
lease is valid. Two jobs started in the **same** instant could still race before either
commits the lease; for hard mutual exclusion under heavy parallelism, run one scheduler
replica or add an orchestrator / GCS generation-precondition lock.
"""

from __future__ import annotations

import os
import uuid as _uuid

from google.cloud import bigquery
from google.cloud.bigquery import ScalarQueryParameter
from google.cloud.exceptions import NotFound

from .settings import DATASET_ID, GCP_PROJECT_ID, _env_int

LOCK_TABLE = "RAW_APIF_INGEST_LOCK"
LOCK_NAME = "api_football"


def ingest_lock_table_id() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{LOCK_TABLE}"


def skip_ingest_lock() -> bool:
    return os.getenv("API_FOOTBALL_SKIP_INGEST_LOCK", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def ensure_ingest_lock_table(client: bigquery.Client) -> None:
    """Create the lock table if needed and ensure the singleton seed row exists."""
    tid = ingest_lock_table_id()
    try:
        client.get_table(tid)
    except NotFound:
        schema = [
            bigquery.SchemaField("lock_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("holder_run_id", "STRING"),
            bigquery.SchemaField("lease_until", "TIMESTAMP"),
            bigquery.SchemaField("acquired_at", "TIMESTAMP"),
        ]
        table = bigquery.Table(tid, schema=schema)
        client.create_table(table, exists_ok=True)
    # If the table existed from an older failed run, it may be empty; always seed.
    client.query(
        f"""
        INSERT INTO `{tid}` (lock_name, holder_run_id, lease_until, acquired_at)
        SELECT @name, NULL, NULL, NULL
        FROM (SELECT 1 AS _singleton)
        WHERE NOT EXISTS (SELECT 1 FROM `{tid}` WHERE lock_name = @name)
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("name", "STRING", LOCK_NAME),
            ]
        ),
    ).result()


def new_run_id() -> str:
    return str(_uuid.uuid4())


def acquire_ingest_lock(
    client: bigquery.Client,
    run_id: str,
    lease_minutes: int | None = None,
) -> bool:
    """
    Try to take the lease. Returns ``True`` if this process holds it.

    Lease is renewed if the same ``run_id`` already holds the lock (idempotent).
    """
    if skip_ingest_lock():
        return True
    mins = lease_minutes if lease_minutes is not None else _env_int("API_FOOTBALL_INGEST_LEASE_MINUTES", 180)
    mins = max(1, mins)
    tid = ingest_lock_table_id()
    job = client.query(
        f"""
        UPDATE `{tid}`
        SET holder_run_id = @run_id,
            lease_until = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL @mins MINUTE),
            acquired_at = CURRENT_TIMESTAMP()
        WHERE lock_name = @lock_name
          AND (
            lease_until IS NULL
            OR lease_until < CURRENT_TIMESTAMP()
            OR holder_run_id = @run_id
          )
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("run_id", "STRING", run_id),
                ScalarQueryParameter("mins", "INT64", mins),
                ScalarQueryParameter("lock_name", "STRING", LOCK_NAME),
            ]
        ),
    )
    job.result()
    n = job.num_dml_affected_rows
    return bool(n and n > 0)


def release_ingest_lock(client: bigquery.Client, run_id: str) -> None:
    """Expire the lease immediately if we still hold it (best-effort)."""
    if skip_ingest_lock():
        return
    tid = ingest_lock_table_id()
    try:
        client.get_table(tid)
    except NotFound:
        return
    client.query(
        f"""
        UPDATE `{tid}`
        SET lease_until = CURRENT_TIMESTAMP()
        WHERE lock_name = @lock_name
          AND holder_run_id = @run_id
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("run_id", "STRING", run_id),
                ScalarQueryParameter("lock_name", "STRING", LOCK_NAME),
            ]
        ),
    ).result()
