"""One-time backfill: populate fixture_id column in RAW_APIF_FIXTURE_DETAILS.

Background
----------
Bug #297: _insert_fixture_rows in batch_fixtures.py omitted fixture_id from
the NDJSON dict and LoadJobConfig schema when writing to RAW_APIF_FIXTURE_DETAILS.
All rows written during wave 1-5 onboarding (2026-05) have fixture_id = NULL.

This script fixes the existing data with a single BQ DML UPDATE and then reports
the remaining NULL count to confirm the update landed.

The staging models extract fixture_id via JSON_VALUE(payload, '$.fixture.id'), so
they produce correct results even with NULL in the column — this backfill is about
correctness and BQ-level filtering efficiency, not about recovering lost data.

Usage
-----
    python scripts/diagnostics/backfill_fixture_ids.py [--dry-run]

Options
-------
    --dry-run   Print the SQL and NULL counts without executing the UPDATE.

Safety
------
    - Only updates rows WHERE fixture_id IS NULL — rows already correct are untouched.
    - Rows where JSON_VALUE(payload, '$.fixture.id') is also NULL (malformed payload)
      are left as NULL; they would fail staging anyway.
    - Run idempotently: re-running after completion is a safe no-op (0 rows updated).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from google.cloud import bigquery

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from ingestion.api_football.settings import GCP_PROJECT_ID, DATASET_ID, raw_table  # noqa: E402


def _table_id() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('FIXTURE_DETAILS')}"


def _count_nulls(client: bigquery.Client, table: str) -> int:
    q = f"SELECT COUNT(*) AS n FROM `{table}` WHERE fixture_id IS NULL"
    rows = list(client.query(q).result())
    return int(rows[0].n)


def _count_total(client: bigquery.Client, table: str) -> int:
    q = f"SELECT COUNT(*) AS n FROM `{table}`"
    rows = list(client.query(q).result())
    return int(rows[0].n)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill fixture_id column in RAW_APIF_FIXTURE_DETAILS (bug #297).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL and counts without executing the UPDATE.",
    )
    args = parser.parse_args()

    client = bigquery.Client(project=GCP_PROJECT_ID)
    table = _table_id()

    print(f"\nTarget table: {table}")

    total = _count_total(client, table)
    nulls_before = _count_nulls(client, table)
    print(f"Total rows   : {total:,}")
    print(f"NULL fixture_id (before): {nulls_before:,}")

    if nulls_before == 0:
        print("\nNothing to backfill — fixture_id is already populated for all rows.")
        return

    update_sql = f"""
UPDATE `{table}`
SET fixture_id = CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64)
WHERE fixture_id IS NULL
  AND JSON_VALUE(payload, '$.fixture.id') IS NOT NULL
"""

    print(f"\nSQL to execute:\n{update_sql.strip()}")

    if args.dry_run:
        print("\n[DRY RUN] Not executing UPDATE. Re-run without --dry-run to apply.")
        return

    print("\nExecuting UPDATE …")
    job = client.query(update_sql)
    job.result()
    print(f"DML complete. Rows affected: {job.num_dml_affected_rows:,}")

    nulls_after = _count_nulls(client, table)
    print(f"NULL fixture_id (after) : {nulls_after:,}")

    if nulls_after == 0:
        print("\nBackfill complete — all rows now have fixture_id populated.")
    else:
        remaining = nulls_after
        print(
            f"\nWARNING: {remaining:,} row(s) still have fixture_id = NULL. "
            f"These rows have no $.fixture.id in their payload and are malformed — "
            f"they would produce no output in staging either. Investigate separately."
        )


if __name__ == "__main__":
    main()
