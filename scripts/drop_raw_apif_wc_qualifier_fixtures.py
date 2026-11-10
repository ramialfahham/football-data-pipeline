"""Drop the unwritten RAW_APIF_WC_QUALIFIER_FIXTURES table; dry-run unless --apply."""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"
TABLE = "RAW_APIF_WC_QUALIFIER_FIXTURES"


def main(apply: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{TABLE}"
    try:
        client.get_table(table_id)
    except NotFound:
        print(f"  SKIP {table_id} (already gone)")
        return

    if not apply:
        print(f"  would drop {table_id} (pass --apply to delete)")
        return

    try:
        client.delete_table(table_id)
        print(f"  dropped {table_id}")
    except Exception as e:
        print(f"  FAIL {table_id}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the table (default is dry-run).",
    )
    args = parser.parse_args()
    main(apply=args.apply)
