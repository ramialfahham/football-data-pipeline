"""One-time migration: copy per-competition raw tables into unified raw tables.

WHY THIS SCRIPT EXISTS
----------------------
Issue #251 changed the Python ingestion layer to write to unified raw tables
(RAW_APIF_{entity}) shared by all competitions, using a league_code STRING
column as discriminator, instead of per-competition tables (RAW_APIF_{LC}_{entity}).

After #251 merges, new pipeline runs write only to the unified tables. But
RAW_APIF_FIXTURE_DETAILS (the most critical table) is still empty — the batch
fixture ingestion checks this table first to decide which fixtures need fetching,
so an empty table causes every historical fixture to be re-fetched on the next run.

This script must run ONCE, BEFORE the next 04:00 UTC pipeline run after #251
is deployed, to populate the unified tables from the existing per-competition data.

WHAT THIS SCRIPT DOES
---------------------
For each known entity (FIXTURES_NEXT, FIXTURE_DETAILS, ROUNDS, STANDINGS, TEAMS,
LEAGUES, PLAYERS, TRANSFERS, INJURIES, COACHES):

  1. Lists all tables in the dataset that match RAW_APIF_{LC}_{entity}.
  2. Creates the unified table (RAW_APIF_{entity}) if it does not exist yet.
  3. For each source table, inserts rows into the unified table via BigQuery
     INSERT INTO ... SELECT — no Python-side data movement.
  4. Skips a source table if the unified table already has rows for that
     league_code (idempotent — safe to re-run).
  5. Prints a summary of rows copied per table.

FIXTURE_DETAILS also extracts fixture_id from the payload JSON so the merge key
(league_code, fixture_id) is available for the dedup/retry logic in batch_fixtures.py.

WHAT THIS SCRIPT DOES NOT DO
-----------------------------
- It does not drop the legacy per-competition tables. That happens in #256.
- It does not touch dbt models or staging views. That happens in #253.
- It does not modify any Python ingestion code.

HOW TO RUN
----------
From the repository root (requires GOOGLE_APPLICATION_CREDENTIALS or gcloud auth):

    python scripts/migrate_to_unified_raw.py

Flags:
    --dry-run   Print what would be done without executing any queries.
    --entity    Migrate only this entity (e.g. --entity FIXTURE_DETAILS).
    --league    Migrate only this league code (e.g. --league BL1).

SAFETY
------
The INSERT is guarded by a NOT EXISTS check on the target: if the unified table
already has any row with league_code = '<LC>', the source is skipped entirely.
This makes the script safe to re-run after partial failures.
"""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

sys.path.insert(0, ".")
from ingestion.api_football.bigquery import ensure_unified_raw_table
from ingestion.api_football.settings import DATASET_ID, GCP_PROJECT_ID

# Entities that use the standard (league_code, payload, ingested_at) schema.
_STANDARD_ENTITIES = [
    "FIXTURES_NEXT",
    "ROUNDS",
    "STANDINGS",
    "TEAMS",
    "LEAGUES",
    "PLAYERS",
    "TRANSFERS",
    "INJURIES",
    "COACHES",
]

# FIXTURE_DETAILS has an additional fixture_id INT64 column.
_FIXTURE_DETAILS_ENTITY = "FIXTURE_DETAILS"

ALL_ENTITIES = _STANDARD_ENTITIES + [_FIXTURE_DETAILS_ENTITY]


def _list_source_tables(
    client: bigquery.Client,
    entity: str,
) -> list[tuple[str, str]]:
    """Return [(league_code, table_name)] for all RAW_APIF_{LC}_{entity} tables."""
    prefix = f"RAW_APIF_"
    suffix = f"_{entity}"
    results = []
    for table in client.list_tables(f"{GCP_PROJECT_ID}.{DATASET_ID}"):
        name = table.table_id
        if name.startswith(prefix) and name.endswith(suffix):
            middle = name[len(prefix) : -len(suffix)]
            # Skip the unified table itself (no league_code in the middle part).
            if not middle:
                continue
            results.append((middle, name))
    return sorted(results)


def _target_has_league(
    client: bigquery.Client,
    target_table_id: str,
    league_code: str,
) -> bool:
    """Return True if the unified table already has rows for this league_code."""
    try:
        client.get_table(target_table_id)
    except NotFound:
        return False
    q = f"""
        SELECT 1
        FROM `{target_table_id}`
        WHERE league_code = '{league_code}'
        LIMIT 1
    """
    try:
        rows = list(client.query(q).result())
        return len(rows) > 0
    except Exception:
        return False


def _copy_standard(
    client: bigquery.Client,
    source_table_id: str,
    target_table_id: str,
    league_code: str,
    dry_run: bool,
) -> int:
    """INSERT rows from a per-competition table into the unified table.

    Returns number of rows inserted (0 on dry run or skip).
    """
    # Count rows to copy for reporting.
    count_q = f"SELECT COUNT(*) AS n FROM `{source_table_id}`"
    n = list(client.query(count_q).result())[0].n
    if n == 0:
        print(f"  SKIP {source_table_id} — empty source table")
        return 0

    insert_q = f"""
        INSERT INTO `{target_table_id}` (league_code, payload, ingested_at)
        SELECT
          '{league_code}' AS league_code,
          payload,
          ingested_at
        FROM `{source_table_id}`
    """
    print(f"  {'[DRY RUN] ' if dry_run else ''}INSERT {n} rows: {source_table_id} → {target_table_id}")
    if not dry_run:
        client.query(insert_q).result()
    return n


def _copy_fixture_details(
    client: bigquery.Client,
    source_table_id: str,
    target_table_id: str,
    league_code: str,
    dry_run: bool,
) -> int:
    """INSERT FIXTURE_DETAILS rows, extracting fixture_id from payload JSON.

    Returns number of rows inserted (0 on dry run or skip).
    """
    count_q = f"SELECT COUNT(*) AS n FROM `{source_table_id}`"
    n = list(client.query(count_q).result())[0].n
    if n == 0:
        print(f"  SKIP {source_table_id} — empty source table")
        return 0

    insert_q = f"""
        INSERT INTO `{target_table_id}` (league_code, payload, ingested_at, fixture_id)
        SELECT
          '{league_code}' AS league_code,
          payload,
          ingested_at,
          CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64) AS fixture_id
        FROM `{source_table_id}`
    """
    print(f"  {'[DRY RUN] ' if dry_run else ''}INSERT {n} rows: {source_table_id} → {target_table_id}")
    if not dry_run:
        client.query(insert_q).result()
    return n


def migrate_entity(
    client: bigquery.Client,
    entity: str,
    *,
    league_filter: str | None,
    dry_run: bool,
) -> None:
    is_fixture_details = entity == _FIXTURE_DETAILS_ENTITY
    target_name = f"RAW_APIF_{entity}"
    target_table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{target_name}"

    sources = _list_source_tables(client, entity)
    if not sources:
        print(f"\n[{entity}] No per-competition source tables found — skipping.")
        return

    if league_filter:
        sources = [(lc, tbl) for lc, tbl in sources if lc == league_filter]
        if not sources:
            print(f"\n[{entity}] No source table for league_filter={league_filter!r} — skipping.")
            return

    print(f"\n[{entity}] {len(sources)} source tables → {target_name}")

    if not dry_run:
        ensure_unified_raw_table(client, target_name, include_fixture_id=is_fixture_details)

    total = 0
    skipped = 0
    for league_code, source_name in sources:
        source_table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{source_name}"

        if not dry_run and _target_has_league(client, target_table_id, league_code):
            print(f"  SKIP {source_name} — {league_code} already present in {target_name}")
            skipped += 1
            continue

        if is_fixture_details:
            n = _copy_fixture_details(client, source_table_id, target_table_id, league_code, dry_run)
        else:
            n = _copy_standard(client, source_table_id, target_table_id, league_code, dry_run)
        total += n

    print(f"[{entity}] done — {total} rows inserted, {skipped} league(s) already present.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without executing queries.")
    parser.add_argument("--entity", metavar="ENTITY", help="Migrate only this entity (e.g. FIXTURE_DETAILS).")
    parser.add_argument("--league", metavar="LC", help="Migrate only this league code (e.g. BL1).")
    args = parser.parse_args()

    if args.entity and args.entity not in ALL_ENTITIES:
        print(f"ERROR: unknown entity {args.entity!r}. Valid: {', '.join(ALL_ENTITIES)}")
        sys.exit(1)

    client = bigquery.Client(project=GCP_PROJECT_ID)
    entities = [args.entity] if args.entity else ALL_ENTITIES

    print(f"migrate_to_unified_raw — project={GCP_PROJECT_ID} dataset={DATASET_ID}")
    if args.dry_run:
        print("DRY RUN — no data will be written.")
    if args.league:
        print(f"league filter: {args.league}")

    for entity in entities:
        migrate_entity(client, entity, league_filter=args.league, dry_run=args.dry_run)

    print("\nMigration complete.")


if __name__ == "__main__":
    main()
