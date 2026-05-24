"""BigQuery helpers: dataset setup, partitioned table creation, and row writes.

Raw tables use an append-only pattern: each pipeline run writes one new row
containing the API response for that run. Tables are partitioned by the date
of ingestion (ingested_at) so BigQuery only scans the relevant day's data
when staging models filter to the latest partition.

The only exception is the per-fixture fanout tables (lineups, events, stats,
fixture players, predictions). These are still written with WRITE_TRUNCATE
until the completeness tracking table migration lands (issue #221), because
each run only fetches a subset of fixtures and we need the merged history
to know what is already covered.
"""

from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .settings import DATASET_ID, GCP_PROJECT_ID

# Module-level cache so we only call create_table() once per table per process.
# This avoids one redundant API call on every subsequent write to the same table.
_partitioned_tables_ensured: set[str] = set()


def _api_football_dataset_location() -> str:
    """Must match dbt `location` in profiles.yml (default EU)."""
    return os.getenv("API_FOOTBALL_DATASET_LOCATION", "EU").strip() or "EU"


def ensure_api_football_dataset(client: bigquery.Client) -> None:
    """Create the raw BigQuery dataset if it does not exist yet.

    Raises RuntimeError if the dataset already exists in a different region,
    because moving datasets between regions requires manual intervention and
    would break all downstream dbt models that reference it.
    """
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


def ensure_raw_table_partitioned(client: bigquery.Client, table_name: str) -> None:
    """Create a raw payload table with date partitioning if it does not exist yet.

    All raw API tables share the same two-column schema:
      - payload    JSON     — the full API response envelope, stored as-is
      - ingested_at TIMESTAMP — when this row was written (UTC)

    The table is partitioned by DATE(ingested_at) so BigQuery only reads the
    relevant day's partition when staging filters to the latest row. Without
    partitioning, every query scans the entire table history.

    If the table already exists this is a no-op (exists_ok=True). We cache
    the result per process so the API call only happens once per table per run.
    """
    if table_name in _partitioned_tables_ensured:
        return

    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    schema = [
        bigquery.SchemaField("payload", "JSON"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    # Partition by the date part of ingested_at — one partition per calendar day.
    # require_partition_filter=False so staging views can still do full scans
    # during development without adding a WHERE clause.
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="ingested_at",
    )
    client.create_table(table, exists_ok=True)
    _partitioned_tables_ensured.add(table_name)


def load_json_to_bq(
    client: bigquery.Client,
    table_name: str,
    payload: dict,
    *,
    as_json_payload: bool = False,
    append: bool = False,
) -> None:
    """Write one JSON row to a BigQuery raw table.

    Two modes:

    as_json_payload=True (used for all API response tables):
        Wraps the payload dict in {"payload": ..., "ingested_at": "<UTC now>"}
        and writes it with an explicit schema. This is necessary because the
        API returns nested arrays and numeric-looking keys that BigQuery's
        autodetect mishandles.

        When append=True, the row is appended to the existing table (WRITE_APPEND)
        and the table is created with date partitioning if it does not exist yet.
        This is the standard mode for reference tables (fixtures, standings, etc.).

        When append=False (legacy), the table is overwritten (WRITE_TRUNCATE).
        This is still used by the fanout tables until issue #221 is complete.

    as_json_payload=False (used for operational tables like INGEST_LOCK):
        Writes the payload dict directly with BigQuery autodetect schema.
        Always uses WRITE_TRUNCATE — these tables hold a single current-state row.
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"

    if as_json_payload:
        if append:
            # Ensure the table exists with date partitioning before the first append.
            # create_table with exists_ok=True is a no-op if the table is already there.
            ensure_raw_table_partitioned(client, table_name)

        ingested_at = datetime.now(timezone.utc).isoformat()
        row = {"payload": payload, "ingested_at": ingested_at}
        line = json.dumps(row, ensure_ascii=True) + "\n"
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("payload", "JSON"),
                bigquery.SchemaField("ingested_at", "TIMESTAMP"),
            ],
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition="WRITE_APPEND" if append else "WRITE_TRUNCATE",
        )
    else:
        line = json.dumps(payload, ensure_ascii=True) + "\n"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,
            write_disposition="WRITE_TRUNCATE",
        )

    job = client.load_table_from_file(
        io.BytesIO(line.encode("utf-8")), table_id, job_config=job_config
    )
    job.result()


def read_latest_payload_json(
    client: bigquery.Client,
    table_name: str,
) -> dict | None:
    """Return the payload from the most recent row in a raw table.

    Used by the fanout loaders (lineups, events, stats, fixture players,
    predictions) to determine which fixtures are already covered before
    deciding what to fetch. After issue #221 introduces the dedicated
    coverage tracking table, this function will no longer be needed for
    completeness checks — but it remains useful for any code that needs
    to inspect the latest API snapshot.

    Returns None if the table does not exist or is empty.

    Implementation note: results are streamed via the BigQuery Storage Read
    API (gRPC) rather than the REST paginator, because merged payload rows
    can exceed REST's 20 MiB per-row response cap on large competitions.
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
    arrow_table = job.result().to_arrow(create_bqstorage_client=True)
    if arrow_table.num_rows == 0:
        return None

    pl = arrow_table.column("payload")[0].as_py()
    if pl is None:
        return None
    if isinstance(pl, dict):
        return pl
    if isinstance(pl, (bytes, bytearray)):
        pl = pl.decode("utf-8")
    if isinstance(pl, str):
        return json.loads(pl)
    return dict(pl)
