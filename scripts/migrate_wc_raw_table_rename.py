"""Rename RAW_WC26_APIF_* tables to RAW_WC_APIF_* in BigQuery.

One-time migration for the WC26 → WC league_code rename.
Run once before deploying the feature/wc-rename dbt changes.

Usage:
    python scripts/migrate_wc_raw_table_rename.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"

TABLES = [
    "RAW_WC26_APIF_FIXTURES_NEXT",
    "RAW_WC26_APIF_LEAGUES",
    "RAW_WC26_APIF_STANDINGS",
    "RAW_WC26_APIF_ROUNDS",
    "RAW_WC26_APIF_TEAMS",
    "RAW_WC26_APIF_INJURIES",
    "RAW_WC26_APIF_TRANSFERS",
    "RAW_WC26_APIF_LINEUPS",
    "RAW_WC26_APIF_FIXTURE_EVENTS",
    "RAW_WC26_APIF_FIXTURE_STATISTICS",
    "RAW_WC26_APIF_FIXTURE_PLAYERS",
    "RAW_WC26_APIF_PREDICTIONS",
    "RAW_WC26_APIF_PLAYERS",
    "RAW_WC26_APIF_QUALIFIER_FIXTURES",
]


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)

    existing = {
        t.table_id
        for t in client.list_tables(f"{PROJECT}.{DATASET}")
    }

    errors: list[str] = []

    for old_name in TABLES:
        new_name = old_name.replace("WC26", "WC")

        if old_name not in existing:
            print(f"SKIP  {old_name} — not found in BigQuery")
            continue

        if new_name in existing:
            print(f"SKIP  {old_name} — target {new_name} already exists")
            continue

        sql = (
            f"ALTER TABLE `{PROJECT}.{DATASET}.{old_name}` "
            f"RENAME TO `{new_name}`"
        )

        if dry_run:
            print(f"DRY   {old_name} -> {new_name}")
        else:
            try:
                client.query(sql).result()
                print(f"OK    {old_name} -> {new_name}")
            except Exception as e:
                errors.append(f"{old_name}: {e}")
                print(f"FAIL  {old_name}: {e}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} error(s). Tables not renamed:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    if not dry_run:
        print("\nAll tables renamed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be renamed without executing.",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
