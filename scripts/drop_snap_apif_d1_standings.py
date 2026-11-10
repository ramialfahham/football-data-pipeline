"""Drop the orphaned snap_apif_d1_standings table; dbt no longer defines that snapshot.

It drops unless --dry-run is given.
"""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"
DATASET = "snapshots"
TABLE = "snap_apif_d1_standings"


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{TABLE}"
    try:
        client.get_table(table_id)
    except NotFound:
        print(f"  SKIP {table_id} (already gone)")
        return

    if dry_run:
        print(f"  would drop {table_id}")
        return

    try:
        client.delete_table(table_id)
        print(f"  dropped {table_id}")
    except Exception as e:
        print(f"  FAIL {table_id}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
