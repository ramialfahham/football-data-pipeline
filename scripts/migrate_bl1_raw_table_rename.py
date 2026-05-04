"""Rename BL1 raw tables to the canonical RAW_APIF_{LEAGUE_CODE}_* format.

Convention: RAW_APIF_{LEAGUE_CODE}_{ENDPOINT}

State in BigQuery before this migration:
  RAW_D1_APIF_*   -- original tables (dbt read these; ingestion stopped writing here
                      when league_code changed from D1 to BL1 in the registry)
  RAW_BL1_APIF_*  -- tables ingestion has been writing to since the registry update;
                      contain the most recent merged data

Migration logic:
  1. Rename RAW_BL1_APIF_* -> RAW_APIF_BL1_* (live data, ingestion destination)
  2. Rename RAW_D1_APIF_*  -> RAW_APIF_BL1_* only for tables that BL1 does not
     already cover (i.e. RAW_APIF_BL1_* target does not exist yet after step 1).
     This handles endpoints that were never re-ingested under the BL1 prefix.

Usage:
    python scripts/migrate_bl1_raw_table_rename.py [--dry-run]
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
    "INGEST_CURSOR",
]

# Step 1: BL1-prefixed tables (recent ingestion) -> correct convention
STEP1 = [(f"RAW_BL1_APIF_{ep}", f"RAW_APIF_BL1_{ep}") for ep in ENDPOINTS]

# Step 2: D1-prefixed tables (stale) -> correct convention, only if target missing
STEP2 = [(f"RAW_D1_APIF_{ep}", f"RAW_APIF_BL1_{ep}") for ep in ENDPOINTS]


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    existing = {t.table_id for t in client.list_tables(f"{PROJECT}.{DATASET}")}
    errors: list[str] = []

    def rename(old: str, new: str) -> None:
        if old not in existing:
            return
        if new in existing:
            print(f"SKIP  {old} -> {new} (target already exists)")
            return
        sql = f"ALTER TABLE `{PROJECT}.{DATASET}.{old}` RENAME TO `{new}`"
        if dry_run:
            print(f"DRY   {old} -> {new}")
        else:
            try:
                client.query(sql).result()
                existing.add(new)
                existing.discard(old)
                print(f"OK    {old} -> {new}")
            except Exception as e:
                errors.append(f"{old}: {e}")
                print(f"FAIL  {old}: {e}", file=sys.stderr)

    print("Step 1: RAW_BL1_APIF_* -> RAW_APIF_BL1_* (recent ingestion data)")
    for old, new in STEP1:
        rename(old, new)

    print("\nStep 2: RAW_D1_APIF_* -> RAW_APIF_BL1_* (historical data, only if target missing)")
    for old, new in STEP2:
        rename(old, new)

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    if not dry_run:
        print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
