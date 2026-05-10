"""Drop every RAW_APIF_*_INJURIES table from BigQuery.

The injuries surface (ingestion call, dbt source, staging model, schema
docs) is fully removed in this PR. This script cleans up the orphaned
raw tables that the previous loader may have created, across every
competition (BL1 + WC qualifier confederations).

Run once after the PR merges. The script lists every table in the raw
dataset whose name ends in ``_INJURIES`` (and starts with the
``RAW_APIF_`` prefix used by the project) and drops each, preserving
non-injury tables.

Usage:
    python scripts/drop_injuries_raw_tables.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"
PREFIX = "RAW_APIF_"
SUFFIX = "_INJURIES"


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    dataset_ref = f"{PROJECT}.{DATASET}"
    try:
        tables = list(client.list_tables(dataset_ref))
    except NotFound:
        print(f"Dataset {dataset_ref} not found.")
        sys.exit(1)

    targets = sorted(
        t.table_id for t in tables
        if t.table_id.startswith(PREFIX) and t.table_id.endswith(SUFFIX)
    )

    if not targets:
        print("No RAW_APIF_*_INJURIES tables found. Nothing to drop.")
        return

    print(f"Found {len(targets)} injury raw table(s) to drop:")
    for name in targets:
        print(f"  - {name}")
    print()

    dropped = 0
    errors: list[str] = []
    for name in targets:
        full_id = f"{PROJECT}.{DATASET}.{name}"
        if dry_run:
            print(f"  would drop {name}")
            continue
        try:
            client.delete_table(full_id)
            print(f"  dropped {name}")
            dropped += 1
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  FAIL {name}: {e}", file=sys.stderr)

    if dry_run:
        print(f"\nDry run: {len(targets)} table(s) would be dropped.")
    else:
        print(f"\nDropped {dropped} of {len(targets)} table(s).")

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
