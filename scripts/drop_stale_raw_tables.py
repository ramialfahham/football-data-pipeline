"""Drop stale BL1 raw tables left over from the D1→BL1 rename migration.

After the rename and merge (PRs #33–#34), all data lives in RAW_APIF_BL1_*
and RAW_APIF_WC_*. Two intermediate table sets are now orphaned:

  RAW_D1_APIF_*    — original D1 tables (13 tables + ODDS)
  RAW_BL1_APIF_*   — intermediate rename target (13 tables)

These are no longer referenced by the ingestion pipeline or dbt models.
Dropping them removes the risk of future runs accidentally writing to them.

Usage:
    cd <repo-root>
    python scripts/drop_stale_raw_tables.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"

STALE_TABLES = [
    # Intermediate rename targets (wrong convention: RAW_BL1_APIF_* instead of RAW_APIF_BL1_*)
    "RAW_BL1_APIF_FIXTURES_NEXT",
    "RAW_BL1_APIF_FIXTURE_EVENTS",
    "RAW_BL1_APIF_FIXTURE_PLAYERS",
    "RAW_BL1_APIF_FIXTURE_STATISTICS",
    "RAW_BL1_APIF_INJURIES",
    "RAW_BL1_APIF_LEAGUES",
    "RAW_BL1_APIF_LINEUPS",
    "RAW_BL1_APIF_PLAYERS",
    "RAW_BL1_APIF_PREDICTIONS",
    "RAW_BL1_APIF_ROUNDS",
    "RAW_BL1_APIF_STANDINGS",
    "RAW_BL1_APIF_TEAMS",
    "RAW_BL1_APIF_TRANSFERS",
    # Original D1 tables (pre-rename, all data merged into RAW_APIF_BL1_*)
    "RAW_D1_APIF_FIXTURES_NEXT",
    "RAW_D1_APIF_FIXTURE_EVENTS",
    "RAW_D1_APIF_FIXTURE_PLAYERS",
    "RAW_D1_APIF_FIXTURE_STATISTICS",
    "RAW_D1_APIF_INJURIES",
    "RAW_D1_APIF_LEAGUES",
    "RAW_D1_APIF_LINEUPS",
    "RAW_D1_APIF_ODDS",
    "RAW_D1_APIF_PLAYERS",
    "RAW_D1_APIF_PREDICTIONS",
    "RAW_D1_APIF_ROUNDS",
    "RAW_D1_APIF_STANDINGS",
    "RAW_D1_APIF_TEAMS",
    "RAW_D1_APIF_TRANSFERS",
]


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    dropped = 0
    skipped = 0
    errors: list[str] = []

    for table_id in STALE_TABLES:
        full_id = f"{PROJECT}.{DATASET}.{table_id}"
        try:
            client.get_table(full_id)
        except NotFound:
            print(f"  SKIP {table_id} (not found)")
            skipped += 1
            continue

        if dry_run:
            print(f"  would drop {table_id}")
            dropped += 1
            continue

        try:
            client.delete_table(full_id)
            print(f"  dropped {table_id}")
            dropped += 1
        except Exception as e:
            errors.append(f"{table_id}: {e}")
            print(f"  FAIL {table_id}: {e}", file=sys.stderr)

    action = "would drop" if dry_run else "dropped"
    print(f"\n{action} {dropped} table(s), skipped {skipped} (already gone).")

    if errors:
        print(f"{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
