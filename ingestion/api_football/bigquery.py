"""BigQuery helpers: dataset setup, partitioned table creation, and row writes.

Raw tables use an append-only pattern: each pipeline run writes one new row
containing the API response for that run. Tables are partitioned by the date
of ingestion (ingested_at) so BigQuery only scans the relevant day's data
when staging models filter to the latest partition.

The per-fixture fanout table (RAW_APIF_FIXTURE_DETAILS) is also append-only:
loads/batch_fixtures.py writes one row per fetched fixture and derives coverage
by reading those rows back (see coverage.py), so no merge step or separate
tracking table is needed. WRITE_TRUNCATE remains only for single-current-state
operational tables (e.g. the ingest lock and the completeness snapshot).
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


def ensure_unified_raw_table(
    client: bigquery.Client,
    table_name: str,
    *,
    include_fixture_id: bool = False,
) -> None:
    """Create a unified raw table (all competitions share it) if it does not exist.

    Schema: league_code STRING, payload JSON, ingested_at TIMESTAMP.
    FIXTURE_DETAILS also has fixture_id INT64 (set include_fixture_id=True).
    Partitioned by DATE(ingested_at), clustered by league_code.
    """
    if table_name in _partitioned_tables_ensured:
        return

    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    schema = [
        bigquery.SchemaField("league_code", "STRING"),
        bigquery.SchemaField("payload", "JSON"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ]
    if include_fixture_id:
        schema.append(bigquery.SchemaField("fixture_id", "INT64"))

    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="ingested_at",
    )
    table.clustering_fields = ["league_code"]
    client.create_table(table, exists_ok=True)
    _partitioned_tables_ensured.add(table_name)


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
    league_code: str | None = None,
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
            if league_code is not None:
                ensure_unified_raw_table(client, table_name)
            else:
                ensure_raw_table_partitioned(client, table_name)

        ingested_at = datetime.now(timezone.utc).isoformat()
        if league_code is not None:
            row = {"league_code": league_code, "payload": payload, "ingested_at": ingested_at}
            schema = [
                bigquery.SchemaField("league_code", "STRING"),
                bigquery.SchemaField("payload", "JSON"),
                bigquery.SchemaField("ingested_at", "TIMESTAMP"),
            ]
        else:
            row = {"payload": payload, "ingested_at": ingested_at}
            schema = [
                bigquery.SchemaField("payload", "JSON"),
                bigquery.SchemaField("ingested_at", "TIMESTAMP"),
            ]
        line = json.dumps(row, ensure_ascii=True) + "\n"
        job_config = bigquery.LoadJobConfig(
            schema=schema,
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


def load_json_payload_rows_to_bq(
    client: bigquery.Client,
    table_name: str,
    payloads: list[dict],
    *,
    league_code: str,
    append: bool = True,
) -> int:
    """Append several JSON payload rows to a unified raw table in ONE atomic load job.

    Each element of ``payloads`` becomes one row ``{league_code, payload, ingested_at}``;
    every row shares a single ``ingested_at`` and the whole batch is written with one
    ``load_table_from_file`` call. A BigQuery load job is all-or-nothing, so the rows
    appear together or not at all — readers that take the latest snapshot as
    ``ingested_at = max(ingested_at) per league_code`` therefore always see a COMPLETE
    chunked snapshot, never a partial one. The shared ``ingested_at`` is microsecond
    precision and ingestion is single-flight (the lease lock admits one run at a time,
    minutes apart), so two distinct snapshots cannot tie on ``ingested_at`` and be merged
    by those readers — every tie is, by construction, the chunks of one snapshot.

    Used when a single snapshot's payload would exceed BigQuery's 100 MB per-row JSON
    limit (RAW_APIF_PLAYERS for large-roster deep leagues — see loads/squads.py). A
    one-element ``payloads`` writes exactly one row, identical to ``load_json_to_bq``.
    Returns the number of rows written (0 for an empty ``payloads``).
    """
    if not payloads:
        return 0
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    if append:
        ensure_unified_raw_table(client, table_name)
    ingested_at = datetime.now(timezone.utc).isoformat()
    schema = [
        bigquery.SchemaField("league_code", "STRING"),
        bigquery.SchemaField("payload", "JSON"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ]
    lines = "".join(
        json.dumps(
            {"league_code": league_code, "payload": p, "ingested_at": ingested_at},
            ensure_ascii=True,
        )
        + "\n"
        for p in payloads
    )
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND" if append else "WRITE_TRUNCATE",
    )
    job = client.load_table_from_file(
        io.BytesIO(lines.encode("utf-8")), table_id, job_config=job_config
    )
    job.result()
    return len(payloads)


def read_latest_payload_json(
    client: bigquery.Client,
    table_name: str,
    league_code: str | None = None,
) -> dict | None:
    """Return the payload from the most recent row in a raw table.

    When ``league_code`` is provided the query is filtered to that league,
    which is required for the unified raw tables (RAW_APIF_FIXTURES_NEXT etc.)
    that store all competitions in one table discriminated by league_code.

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

    league_filter = (
        f" WHERE league_code = '{league_code}'" if league_code else ""
    )
    if "ingested_at" in colnames:
        q = f"SELECT payload FROM `{table_id}`{league_filter} ORDER BY ingested_at DESC LIMIT 1"
    elif "ingested_datetime" in colnames:
        q = f"SELECT payload FROM `{table_id}`{league_filter} ORDER BY ingested_datetime DESC LIMIT 1"
    else:
        q = f"SELECT payload FROM `{table_id}`{league_filter} LIMIT 1"

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
