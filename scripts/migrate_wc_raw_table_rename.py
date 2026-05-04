"""Rename WC raw tables in BigQuery to the canonical RAW_APIF_{LEAGUE_CODE}_* format.

Convention: RAW_APIF_{LEAGUE_CODE}_{ENDPOINT}
  correct : RAW_APIF_WC_FIXTURES_NEXT
  wrong   : RAW_WC26_APIF_FIXTURES_NEXT  (embedded season year, wrong order)
  wrong   : RAW_WC_APIF_FIXTURES_NEXT    (wrong order)

This script handles both intermediate states so it is safe to run regardless
of which step was reached previously.

Usage:
    python scripts/migrate_wc_raw_table_rename.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"

ENDPOINTS = [
    "FIXTURES_NEXT",
    "LEAGUES",
    "STANDINGS",
    "ROUNDS",
    "TEAMS",
    "INJURIES",
    "TRANSFERS",
    "LINEUPS",
    "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS",
    "PREDICTIONS",
    "PLAYERS",
    "QUALIFIER_FIXTURES",
]

# All intermediate names that must end up as RAW_APIF_WC_{endpoint}.
RENAMES: list[tuple[str, str]] = [
    (f"RAW_WC26_APIF_{ep}", f"RAW_APIF_WC_{ep}") for ep in ENDPOINTS
] + [
    (f"RAW_WC_APIF_{ep}", f"RAW_APIF_WC_{ep}") for ep in ENDPOINTS
]


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)

    existing = {t.table_id for t in client.list_tables(f"{PROJECT}.{DATASET}")}

    errors: list[str] = []

    for old_name, new_name in RENAMES:
        if old_name not in existing:
            continue
        if new_name in existing:
            print(f"SKIP  {old_name} -> {new_name} (target already exists)")
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
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    if not dry_run:
        print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
