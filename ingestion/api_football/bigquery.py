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
    # require_partition_filter=False so staging models can still do full scans
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
    ingested_at: str | None = None,
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

    Pass ``ingested_at`` (UTC ISO string) when the caller needs the exact timestamp
    afterwards — a merge-on-write that deletes the rows superseded by this load must
    delete strictly BEFORE it, and cannot do that if the stamp is invented in here and
    thrown away. Mirrors the same parameter on ``load_json_payload_rows_to_bq``. Ignored
    when ``as_json_payload=False``, which writes the payload dict verbatim.
    """
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
    """Append several JSON payload rows to a unified raw table in ONE atomic load job.

    Each element of ``payloads`` becomes one row ``{league_code, payload, ingested_at}``,
    all sharing one ``ingested_at`` and written with a single ``load_table_from_file`` call
    (all-or-nothing). Used to store a snapshot as MANY small rows instead of one oversized
    row — e.g. RAW_APIF_PLAYERS writes one row per (team, season) so no single row can
    approach BigQuery's 100 MB per-row JSON limit (mirrors RAW_APIF_FIXTURE_DETAILS, which
    stores one row per fixture). Pass ``ingested_at`` (UTC ISO string) when the caller needs
    the exact timestamp afterwards — e.g. a merge-on-write that deletes superseded rows
    written before this load. Returns the number of rows written (0 for empty input).
    """
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


def delete_superseded_league_rows(
    client: bigquery.Client,
    table_name: str,
    league_code: str,
    before: datetime,
) -> None:
    """Drop this league's rows written before ``before`` — the whole-league merge-on-write.

    For raw tables whose loader writes ONE row covering the entire league (TRANSFERS,
    STANDINGS, TEAMS), so the row just appended fully supersedes every earlier one and
    staging's latest-per-league ``qualify`` was already discarding them. #33 item 8b.

    The per-key sibling is ``loads/squads.py:_delete_superseded_player_rows``, which keeps a
    ``(team, season)`` predicate because RAW_APIF_PLAYERS holds many rows per league and a
    bare league delete there would drop keys this run did not re-fetch. The difference is the
    row grain, not a preference — do NOT copy this function to a multi-row-per-league table.

    Call it only AFTER the append succeeded and only when the fetch was COMPLETE (the #896
    guard from 8a returns early otherwise). ``before`` must be the appended row's own
    ``ingested_at``, so the strict ``<`` leaves that row intact.

    Both predicates prune: the table is clustered on ``league_code`` and DAY-partitioned on
    ``ingested_at`` (``ensure_unified_raw_table``).
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    q = f"""
        delete from `{table_id}`
        where league_code = @lc
          and ingested_at < @before
    """
    client.query(
        q,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("lc", "STRING", league_code),
                bigquery.ScalarQueryParameter("before", "TIMESTAMP", before),
            ]
        ),
    ).result()


def _scalar(
    client: bigquery.Client,
    sql: str,
    params: list[bigquery.ScalarQueryParameter],
):
    """Run a one-cell query and return that cell, or None when there is no row.

    Kept separate so the cheap timestamp lookup in read_latest_payload_json cannot accidentally be
    routed through the Storage Read API path below it, which exists for multi-megabyte payload rows
    and is pure overhead for a single scalar.
    """
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
    """Return the payload from the most recent row in a raw table.

    When ``league_code`` is provided the query is filtered to that league,
    which is required for the unified raw tables (RAW_APIF_FIXTURES_NEXT etc.)
    that store all competitions in one table discriminated by league_code.

    Returns None if the table does not exist or is empty.

    Reads in TWO steps when the table has an ingest-time column, because that column is the
    partition key and it is the only shape that prunes (#890). The reasoning and the measured
    numbers are at the call site below, next to the queries they describe.

    Implementation note: the PAYLOAD result is streamed via the BigQuery Storage Read
    API (gRPC) rather than the REST paginator, because merged payload rows
    can exceed REST's 20 MiB per-row response cap on large competitions. The timestamp
    lookup deliberately does not use that path -- see ``_scalar``.
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        table = client.get_table(table_id)
    except NotFound:
        return None

    colnames = {f.name for f in table.schema}
    if "payload" not in colnames:
        return None

    # Which column carries the ingest time, if any. It is the PARTITION column on the raw tables.
    ts_col = (
        "ingested_at" if "ingested_at" in colnames
        else "ingested_datetime" if "ingested_datetime" in colnames
        else None
    )

    # The parameter type has to match the column: `ingested_at` is TIMESTAMP but a table using
    # `ingested_datetime` may be DATETIME, and a mismatched parameter is a query error rather than
    # a wrong answer. Read it from the schema instead of assuming.
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
        # No ingest-time column, so there is no partition to prune to. Unchanged behaviour.
        q = f"SELECT payload FROM `{table_id}`{_where()} LIMIT 1"
    else:
        # TWO queries, deliberately (#890). `ORDER BY {ts_col} DESC LIMIT 1` returns one row but
        # cannot prune partitions: to rank, BigQuery reads every partition ever written, on the
        # widest column in the warehouse. Measured by dry run on RAW_APIF_TRANSFERS/BL1:
        #   ORDER BY ... LIMIT 1                          6.634 GiB
        #   MAX({ts_col}) alone                           0.013 MiB   <- reads one narrow column
        #   payload WHERE {ts_col} = <literal>            2.95  MiB   <- prunes to one partition
        # A subquery predicate (`= (SELECT MAX(...))`) was measured too and scans the SAME
        # 6.634 GiB, because BigQuery does not prune on a subquery. So one round trip cannot work;
        # the extra call costs 13 KB and saves gigabytes.
        latest = _scalar(
            client,
            f"SELECT MAX({ts_col}) AS ts FROM `{table_id}`{_where()}",
            params,
        )
        if latest is None:
            # No rows for this league at all. The second query would return nothing, so skip it.
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
