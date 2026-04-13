"""BigQuery dataset ensure + single-row NDJSON loads."""

from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .config import DATASET_ID, GCP_PROJECT_ID


def _api_football_dataset_location() -> str:
    """Must match dbt `location` in profiles.yml (default EU)."""
    return os.getenv("API_FOOTBALL_DATASET_LOCATION", "EU").strip() or "EU"


def ensure_api_football_dataset(client: bigquery.Client) -> None:
    ref = f"{GCP_PROJECT_ID}.{DATASET_ID}"
    want_loc = _api_football_dataset_location()
    try:
        existing = client.get_dataset(ref)
        got = (existing.location or "").upper()
        if got and got != want_loc.upper():
            raise RuntimeError(
                f"BigQuery dataset {ref} exists in location {existing.location!r} but "
                f"API_FOOTBALL_DATASET_LOCATION / dbt expect {want_loc!r}. "
                f"Delete dataset {DATASET_ID} in the console (or pick one region everywhere), then re-run."
            )
        return
    except NotFound:
        pass
    ds = bigquery.Dataset(ref)
    ds.location = want_loc
    client.create_dataset(ds, exists_ok=True)


def load_json_to_bq(
    client: bigquery.Client,
    table_name: str,
    payload: dict,
    *,
    as_json_payload: bool = False,
) -> None:
    """Load one NDJSON row into ``table_name``.

    ``as_json_payload=True`` stores the API envelope (or batched wrapper) in ``payload`` (JSON)
    plus ``ingested_datetime`` (UTC load time). Use for responses where autodetect fails (nested arrays, numeric-looking keys).
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    if as_json_payload:
        ingested_datetime = datetime.now(timezone.utc).isoformat()
        row = {"payload": payload, "ingested_datetime": ingested_datetime}
        line = json.dumps(row, ensure_ascii=True) + "\n"
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("payload", "JSON"),
                bigquery.SchemaField("ingested_datetime", "TIMESTAMP"),
            ],
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition="WRITE_TRUNCATE",
        )
    else:
        line = json.dumps(payload, ensure_ascii=True) + "\n"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,
            write_disposition="WRITE_TRUNCATE",
        )
    job = client.load_table_from_file(io.BytesIO(line.encode("utf-8")), table_id, job_config=job_config)
    job.result()
