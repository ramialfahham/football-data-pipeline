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
    plus ``ingested_at`` (UTC load time). Use for responses where autodetect fails (nested arrays, numeric-looking keys).
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    if as_json_payload:
        ingested_at = datetime.now(timezone.utc).isoformat()
        row = {"payload": payload, "ingested_at": ingested_at}
        line = json.dumps(row, ensure_ascii=True) + "\n"
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("payload", "JSON"),
                bigquery.SchemaField("ingested_at", "TIMESTAMP"),
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


def read_latest_payload_json(
    client: bigquery.Client,
    table_name: str,
) -> dict | None:
    """
    Return the ``payload`` JSON object from the latest row (by ``ingested_at`` when
    that column exists, else ``ingested_datetime`` for tables not yet migrated;
    otherwise ``LIMIT 1`` for legacy autodetect tables).

    Used to merge this run's data with prior loads so raw tables stay complete across
    quota-limited runs. Returns ``None`` if the table is missing or empty.
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        table = client.get_table(table_id)
    except NotFound:
        return None
    colnames = {f.name for f in table.schema}
    if "payload" not in colnames:
        return None
    if "ingested_at" in colnames:
        q = f"SELECT payload FROM `{table_id}` ORDER BY ingested_at DESC LIMIT 1"
    elif "ingested_datetime" in colnames:
        q = f"SELECT payload FROM `{table_id}` ORDER BY ingested_datetime DESC LIMIT 1"
    else:
        q = f"SELECT payload FROM `{table_id}` LIMIT 1"
    job = client.query(q)
    rows = list(job.result())
    if not rows:
        return None
    row = rows[0]
    pl = row["payload"] if "payload" in row.keys() else row[0]
    if pl is None:
        return None
    if isinstance(pl, dict):
        return pl
    if isinstance(pl, str):
        return json.loads(pl)
    return dict(pl)
