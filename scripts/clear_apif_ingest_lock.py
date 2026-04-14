"""One-off: expire the API-Football BigQuery ingest lease (stale lock after crash)."""

from __future__ import annotations

import os
import sys

# Repo root on path for ingestion.config
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from ingestion.api_football.config import GCP_PROJECT_ID
from ingestion.api_football.ingestion_lock import (
    LOCK_NAME,
    ensure_ingest_lock_table,
    ingest_lock_table_id,
)


def main() -> None:
    tid = ingest_lock_table_id()
    client = bigquery.Client(project=GCP_PROJECT_ID)
    ensure_ingest_lock_table(client)
    try:
        client.get_table(tid)
    except NotFound:
        print(f"No lock table after ensure ({tid}); abort.")
        return
    q = f"""
    UPDATE `{tid}`
    SET
      holder_run_id = NULL,
      lease_until = TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY),
      acquired_at = CURRENT_TIMESTAMP()
    WHERE lock_name = @lock_name
    """
    job = client.query(
        q,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("lock_name", "STRING", LOCK_NAME),
            ]
        ),
    )
    job.result()
    print(f"Cleared ingest lock {tid} (dml_affected_rows={job.num_dml_affected_rows}).")


if __name__ == "__main__":
    main()
