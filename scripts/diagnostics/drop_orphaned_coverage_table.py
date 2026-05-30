"""Drop the orphaned RAW_APIF_FIXTURE_COVERAGE table (one-time cleanup for issue #221).

Background
----------
RAW_APIF_FIXTURE_COVERAGE was a tracking table that recorded which
(league_code, fixture_id, endpoint) combinations had been fetched. It was a
denormalized mirror of data already held in RAW_APIF_FIXTURE_DETAILS, and the
live daily pipeline never wrote to it — only a manual backfill script did, and
that script read per-competition raw tables that were later dropped (#256/#280).

The coverage-table mechanism was removed in the PR that retired it: fanout
coverage is now derived directly from RAW_APIF_FIXTURE_DETAILS (see
ingestion/api_football/coverage.py). After that PR is deployed, nothing creates,
reads, or writes RAW_APIF_FIXTURE_COVERAGE — the physical table is orphaned and
this script drops it.

When to run
-----------
Run ONCE, AFTER the coverage-retirement PR is merged and deployed. Running it
earlier is pointless: the old code calls ensure_coverage_table() on every run and
would recreate the table on the next scheduled ingest.

Usage
-----
    python scripts/diagnostics/drop_orphaned_coverage_table.py [--dry-run]

Options
-------
    --dry-run   Report whether the table exists, without dropping it.

Safety
------
    - Only ever touches RAW_APIF_FIXTURE_COVERAGE — no other table.
    - Idempotent: a no-op (and exit 0) if the table is already gone.
    - BigQuery time travel retains the dropped table for ~7 days if recovery is
      ever needed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from ingestion.api_football.settings import GCP_PROJECT_ID, DATASET_ID  # noqa: E402

COVERAGE_TABLE = "RAW_APIF_FIXTURE_COVERAGE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report whether the table exists, without dropping it.",
    )
    args = parser.parse_args()

    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{COVERAGE_TABLE}"
    client = bigquery.Client(project=GCP_PROJECT_ID)

    try:
        client.get_table(table_id)
    except NotFound:
        print(f"OK: {table_id} does not exist — nothing to drop.")
        return 0

    if args.dry_run:
        print(f"DRY RUN: {table_id} exists and would be dropped.")
        return 0

    client.delete_table(table_id, not_found_ok=True)
    print(f"Dropped {table_id}. (Recoverable via BigQuery time travel for ~7 days.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
