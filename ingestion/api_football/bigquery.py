"""BigQuery helpers: dataset setup, partitioned raw table creation and append-only row writes."""

from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .settings import DATASET_ID, GCP_PROJECT_ID

# Per-process cache so create_table() runs once per table.
_partitioned_tables_ensured: set[str] = set()


def _api_football_dataset_location() -> str:
    """Must match dbt `location` in profiles.yml (default EU)."""
    return os.getenv("API_FOOTBALL_DATASET_LOCATION", "EU").strip() or "EU"


def ensure_api_football_dataset(client: bigquery.Client) -> None:
    """Create the raw dataset; raises if it exists in another region, which dbt would not follow."""
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
    """Create a unified raw table shared by all competitions, partitioned by ingest day."""
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
    """Create a payload-only raw table partitioned by ingest day, so latest-row reads prune."""
    if table_name in _partitioned_tables_ensured:
        return

    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    schema = [
        bigquery.SchemaField("payload", "JSON"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ]
    table = bigquery.Table(table_id, schema=schema)
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
    append: bool,
    league_code: str | None = None,
    ingested_at: str | None = None,
) -> None:
    """Write one row; append=False truncates the whole table, so it stays a required keyword."""
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"

    if as_json_payload:
        if append:
            if league_code is not None:
                ensure_unified_raw_table(client, table_name)
            else:
                ensure_raw_table_partitioned(client, table_name)

        ingested_at = ingested_at or datetime.now(timezone.utc).isoformat()
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
    ingested_at: str | None = None,
) -> int:
    """Write each payload as its own row in one atomic load, staying under the per-row limit."""
    if not payloads:
        return 0
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    if append:
        ensure_unified_raw_table(client, table_name)
    ingested_at = ingested_at or datetime.now(timezone.utc).isoformat()
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


# Raw tables are append-only and never deleted from; the base layer decides which rows win.


def _scalar(
    client: bigquery.Client,
    sql: str,
    params: list[bigquery.ScalarQueryParameter],
):
    """Run a one-cell query via REST, since the Storage Read API is overhead for a single scalar."""
    rows = list(
        client.query(
            sql, job_config=bigquery.QueryJobConfig(query_parameters=params)
        ).result()
    )
    return rows[0][0] if rows else None


def read_latest_payload_json(
    client: bigquery.Client,
    table_name: str,
    league_code: str | None = None,
) -> dict | None:
    """Latest payload or None, read via the Storage Read API to pass REST's 20 MiB row cap."""
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        table = client.get_table(table_id)
    except NotFound:
        return None

    colnames = {f.name for f in table.schema}
    if "payload" not in colnames:
        return None

    ts_col = (
        "ingested_at" if "ingested_at" in colnames
        else "ingested_datetime" if "ingested_datetime" in colnames
        else None
    )

    # The parameter type must match the column, which may be DATETIME rather than TIMESTAMP.
    ts_type = next((f.field_type for f in table.schema if f.name == ts_col), None) if ts_col else None

    conditions: list[str] = []
    params: list[bigquery.ScalarQueryParameter] = []
    if league_code:
        conditions.append("league_code = @league_code")
        params.append(bigquery.ScalarQueryParameter("league_code", "STRING", league_code))

    def _where(extra: list[str] | None = None) -> str:
        clauses = conditions + (extra or [])
        return (" WHERE " + " AND ".join(clauses)) if clauses else ""

    if ts_col is None:
        q = f"SELECT payload FROM `{table_id}`{_where()} LIMIT 1"
    else:
        # Two queries: ORDER BY LIMIT 1 and a MAX() subquery both scan every partition, while a
        # literal predicate on the partition column prunes to one.
        latest = _scalar(
            client,
            f"SELECT MAX({ts_col}) AS ts FROM `{table_id}`{_where()}",
            params,
        )
        if latest is None:
            return None
        q = f"SELECT payload FROM `{table_id}`{_where([f'{ts_col} = @ts'])} LIMIT 1"
        params = params + [
            bigquery.ScalarQueryParameter("ts", ts_type or "TIMESTAMP", latest)
        ]

    job = client.query(q, job_config=bigquery.QueryJobConfig(query_parameters=params))
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
