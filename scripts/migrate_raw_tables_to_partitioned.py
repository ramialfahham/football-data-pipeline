"""One-time migration: recreate raw API tables with date partitioning.

WHY THIS SCRIPT EXISTS
----------------------
Before this migration, raw tables stored all historical data in a single JSON
row using a merge-on-write pattern. BigQuery cannot add partitioning to an
existing table, so we need to recreate each table with the correct partition
spec while preserving its existing data.

After this migration, tables are partitioned by DATE(ingested_at). Each daily
pipeline run appends one new row, and BigQuery only scans the relevant day's
partition when staging models filter to the latest row.

WHAT THIS SCRIPT DOES
---------------------
For each raw table that has both a `payload` column and an `ingested_at` column
(i.e. every API response table, not operational tables like INGEST_LOCK):

  1. Check whether the table is already partitioned. If yes, skip it — the
     script is safe to run multiple times.
  2. Recreate the table with PARTITION BY DATE(ingested_at) using a BigQuery
     CTAS (CREATE OR REPLACE TABLE ... AS SELECT ...). BigQuery reads the
     current rows, creates the new partitioned table, and copies the data in
     one atomic operation.

WHAT THIS SCRIPT DOES NOT DO
-----------------------------
- It does not touch fanout tables any differently than reference tables.
  All raw tables get partitioned here. The fanout tables will keep using
  WRITE_TRUNCATE (overwriting the table) until issue #221 switches them to
  append-only. Having partitioning on a WRITE_TRUNCATE table is harmless —
  WRITE_TRUNCATE drops and recreates all partitions, which is equivalent to
  recreating the whole table.

- It does not touch dbt models, staging views, or any other layer. Those
  changes are in their own issues (#222 staging, #223 core).

HOW TO RUN
----------
From the repository root:

    python scripts/migrate_raw_tables_to_partitioned.py

Requires the standard GCP authentication environment (GOOGLE_APPLICATION_CREDENTIALS
or application default credentials). The same credentials used by the daily
pipeline are sufficient.

This script is safe to re-run: already-partitioned tables are skipped.
"""

from __future__ import annotations

import sys

from google.cloud import bigquery

# These constants match the values used by the ingestion package.
GCP_PROJECT = "football-data-pipeline-gcp"
DATASET_ID = "raw"
LOCATION = "EU"

# Operational tables that do not use the payload+ingested_at schema.
# We skip these because they serve a different purpose and do not need
# date partitioning.
SKIP_TABLES = {
    "RAW_APIF_INGEST_LOCK",
}


def _table_is_partitioned(table: bigquery.Table) -> bool:
    """Return True if the table already has date partitioning configured."""
    return table.time_partitioning is not None


def _table_has_required_columns(table: bigquery.Table) -> bool:
    """Return True if the table has both payload and ingested_at columns.

    These are the two columns present on every API response table. Tables
    without these columns (e.g. operational tables) are left untouched.
    """
    col_names = {f.name for f in table.schema}
    return "payload" in col_names and "ingested_at" in col_names


def migrate_table(client: bigquery.Client, table_id: str) -> str:
    """Recreate one table with date partitioning, preserving existing data.

    Returns a status string: 'skipped', 'already_partitioned', or 'migrated'.
    """
    table_name = table_id.split(".")[-1]

    if table_name in SKIP_TABLES:
        return "skipped"

    try:
        table = client.get_table(table_id)
    except Exception as e:
        print(f"  WARNING: could not read {table_id}: {e}", file=sys.stderr)
        return "skipped"

    if not _table_has_required_columns(table):
        return "skipped"

    if _table_is_partitioned(table):
        return "already_partitioned"

    # Recreate the table with partitioning using a CTAS.
    #
    # CREATE OR REPLACE TABLE reads from the current table, creates a new
    # partitioned version, and replaces the original — all in one BigQuery
    # operation. The existing row(s) are preserved, landing in the partition
    # that matches their ingested_at date.
    ddl = f"""
        CREATE OR REPLACE TABLE `{table_id}`
        PARTITION BY DATE(ingested_at)
        OPTIONS (require_partition_filter = false)
        AS
        SELECT payload, ingested_at
        FROM `{table_id}`
    """
    job = client.query(ddl)
    job.result()  # wait for completion
    return "migrated"


def main() -> None:
    client = bigquery.Client(project=GCP_PROJECT)
    dataset_ref = f"{GCP_PROJECT}.{DATASET_ID}"

    print(f"Scanning tables in {dataset_ref} (location={LOCATION}) ...")
    tables = list(client.list_tables(dataset_ref))
    print(f"Found {len(tables)} tables.\n")

    counts = {"migrated": 0, "already_partitioned": 0, "skipped": 0}

    for table_item in sorted(tables, key=lambda t: t.table_id):
        table_id = f"{GCP_PROJECT}.{DATASET_ID}.{table_item.table_id}"
        status = migrate_table(client, table_id)
        counts[status] += 1

        symbol = {"migrated": "✓", "already_partitioned": "–", "skipped": " "}.get(status, "?")
        print(f"  [{symbol}] {table_item.table_id}  ({status})")

    print(
        f"\nDone. "
        f"Migrated: {counts['migrated']}  "
        f"Already partitioned: {counts['already_partitioned']}  "
        f"Skipped: {counts['skipped']}"
    )

    if counts["migrated"] > 0:
        print(
            "\nNext step: run the pipeline once to verify that appended rows "
            "land in the correct partitions, then check staging row counts."
        )


if __name__ == "__main__":
    main()
