"""Seed RAW_APIF_FIXTURE_COVERAGE from existing fanout raw table data.

WHY THIS SCRIPT EXISTS
----------------------
Issue #221 introduces RAW_APIF_FIXTURE_COVERAGE — a tracking table that records
which (league_code, fixture_id, endpoint) combinations have already been fetched.
The fanout pipeline reads this table at startup instead of parsing merged JSON
blobs to determine what is already covered.

Without this migration, the coverage table starts empty. The first pipeline run
after deploying #221 would see every fixture as uncovered and re-fetch all five
endpoints for every historical fixture — burning the entire daily API quota on
work that has already been done.

IMPORTANT — TWO PIPELINE GENERATIONS
--------------------------------------
This script handles both the old merge-on-write pipeline and the current
append-only pipeline:

OLD (merge-on-write, pre-#220):
  Each raw fanout table had a single row (or one fully-merged blob) containing
  all historically fetched fixtures in its response array.

CURRENT (append-only, post-#220):
  Each daily run appends a NEW row containing only that run's fetches.
  The table can have many rows, each covering a different subset of fixtures.

WARNING: Do NOT revert to reading only the latest row (LIMIT 1). That was correct
for the old pipeline where the latest blob was fully merged. Under append-only,
LIMIT 1 silently misses every fixture fetched before the most recent run.
This script reads ALL rows and unions fixture_ids across all ingestion dates.

This was the root cause of issue #240: WCQ leagues onboarded after the
append-only migration had fixture_statistics data in their raw tables but zero
entries in RAW_APIF_FIXTURE_COVERAGE, causing daily re-fetching of already-covered
fixtures and duplicate rows in the raw tables.

WHAT THIS SCRIPT DOES
---------------------
For each active competition in the registry and each of the five fanout endpoints:

  1. Read ALL rows from the raw fanout table (e.g. RAW_APIF_WCQEU_FIXTURE_STATISTICS).
  2. Across all rows, collect the union of fixture IDs. For FIXTURE_STATISTICS,
     only count entries where the statistics list is non-empty (matching the rule
     used by the live pipeline when writing coverage rows).
  3. Skip fixture IDs already present in RAW_APIF_FIXTURE_COVERAGE (idempotent).
  4. Write coverage rows for all newly found (league_code, fixture_id, endpoint).

WHAT THIS SCRIPT DOES NOT DO
-----------------------------
- It does not modify the fanout raw tables.
- It does not touch dbt, staging, or any other layer.
- It is safe to re-run: already-covered fixtures are skipped.

HOW TO RUN
----------
From the repository root:

    python scripts/populate_coverage_table.py

To limit to specific leagues (e.g. WCQ only):

    python scripts/populate_coverage_table.py --leagues WCQEU WCQAF WCQCA WCQSA WCQAS WCQIP WCQOC

Requires the standard GCP authentication environment
(GOOGLE_APPLICATION_CREDENTIALS or application default credentials).
"""

from __future__ import annotations

import argparse
import json
import sys

from google.cloud import bigquery

# These constants match the values used by the ingestion package.
GCP_PROJECT = "football-data-pipeline-gcp"
DATASET_ID = "raw"

# Fanout entity names → the payload key used to check non-emptiness.
# FIXTURE_STATISTICS requires a non-empty statistics list; the others are
# considered covered whenever the fixture_id appears in the response.
ENTITY_TO_PAYLOAD_KEY: dict[str, str | None] = {
    "LINEUPS":            None,
    "FIXTURE_EVENTS":     None,
    "FIXTURE_STATISTICS": "statistics",
    "FIXTURE_PLAYERS":    None,
    "PREDICTIONS":        None,
}

# Maps entity names to the endpoint string stored in the coverage table.
ENTITY_TO_ENDPOINT: dict[str, str] = {
    "LINEUPS":            "LINEUPS",
    "FIXTURE_EVENTS":     "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS": "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS":    "FIXTURE_PLAYERS",
    "PREDICTIONS":        "PREDICTIONS",
}


def _raw_table_id(league_code: str, entity: str) -> str:
    return f"{GCP_PROJECT}.{DATASET_ID}.RAW_APIF_{league_code}_{entity}"


def _coverage_table_id() -> str:
    return f"{GCP_PROJECT}.{DATASET_ID}.RAW_APIF_FIXTURE_COVERAGE"


def _collect_covered_fixture_ids(
    client: bigquery.Client,
    table_id: str,
    *,
    required_payload_key: str | None,
) -> set[int] | None:
    """Collect all covered fixture IDs from a raw fanout table across ALL rows.

    Reads every row in the table and unions fixture_ids across all ingestion
    dates. This handles both the old merge-on-write pipeline (one fully-merged
    blob per table) and the current append-only pipeline (one row per daily run).

    For FIXTURE_STATISTICS, a fixture is only counted as covered if its payload
    list for required_payload_key is non-empty — matching the rule used by the
    live pipeline when deciding whether to write a coverage entry.

    Returns None if the table does not exist or has no rows.
    """
    try:
        client.get_table(table_id)
    except Exception:
        return None

    q = f"SELECT payload FROM `{table_id}`"
    try:
        rows = list(client.query(q).result())
    except Exception as e:
        print(f"  WARNING: query failed for {table_id}: {e}", file=sys.stderr)
        return None

    if not rows:
        return None

    out: set[int] = set()
    for bq_row in rows:
        raw = bq_row.payload
        if not raw:
            continue
        # BQ JSON columns are deserialized to dict automatically.
        # Legacy STRING columns need json.loads().
        if isinstance(raw, dict):
            payload = raw
        else:
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError):
                continue
        for item in (payload or {}).get("response") or []:
            fid = item.get("fixture_id")
            if fid is None:
                continue
            if required_payload_key is not None:
                if not item.get(required_payload_key):
                    continue
            try:
                out.add(int(fid))
            except (TypeError, ValueError):
                continue

    return out if out else None


def _table_exists(client: bigquery.Client, table_id: str) -> bool:
    try:
        client.get_table(table_id)
        return True
    except Exception:
        return False


def _read_existing_coverage(
    client: bigquery.Client,
) -> dict[str, dict[str, set[int]]]:
    """Read existing coverage entries to enable idempotent writes.

    Returns covered[league_code][endpoint] = set of fixture_ids.
    """
    coverage_table_id = _coverage_table_id()
    if not _table_exists(client, coverage_table_id):
        return {}
    q = f"SELECT league_code, fixture_id, endpoint FROM `{coverage_table_id}`"
    try:
        rows = list(client.query(q).result())
    except Exception as e:
        print(f"WARNING: could not read existing coverage: {e}", file=sys.stderr)
        return {}
    out: dict[str, dict[str, set[int]]] = {}
    for row in rows:
        out.setdefault(row.league_code, {}).setdefault(row.endpoint, set()).add(int(row.fixture_id))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed RAW_APIF_FIXTURE_COVERAGE from existing raw fanout tables.")
    parser.add_argument(
        "--leagues",
        nargs="+",
        metavar="LEAGUE_CODE",
        help="Limit to specific league codes (e.g. WCQEU WCQAF). Default: all active competitions.",
    )
    args = parser.parse_args()

    sys.path.insert(0, ".")
    from ingestion.api_football.registry import selected_competitions
    from ingestion.api_football.coverage import ensure_coverage_table, write_coverage

    client = bigquery.Client(project=GCP_PROJECT)
    ensure_coverage_table(client)

    # Read what's already in the coverage table so we only write new rows.
    print("Reading existing coverage table...")
    existing = _read_existing_coverage(client)
    total_existing = sum(
        len(fids)
        for endpoints in existing.values()
        for fids in endpoints.values()
    )
    print(f"Found {total_existing:,} existing coverage entries.\n")

    selected, skipped = selected_competitions()

    if args.leagues:
        requested = {lc.upper() for lc in args.leagues}
        selected = [c for c in selected if c.league_code in requested]
        missing = requested - {c.league_code for c in selected}
        if missing:
            print(f"WARNING: leagues not found in registry: {', '.join(sorted(missing))}", file=sys.stderr)

    print(f"Processing {len(selected)} competition(s)...\n")

    all_coverage_rows: list[dict] = []
    totals: dict[str, int] = {}

    for comp in selected:
        lc = comp.league_code
        comp_rows: list[dict] = []

        for entity, endpoint in ENTITY_TO_ENDPOINT.items():
            table_id = _raw_table_id(lc, entity)
            required_key = ENTITY_TO_PAYLOAD_KEY[entity]

            covered_ids = _collect_covered_fixture_ids(
                client, table_id, required_payload_key=required_key
            )
            if covered_ids is None:
                print(f"  [{lc}] {entity}: table missing or empty — skipped")
                continue

            # Skip fixture_ids already in the coverage table.
            already_covered = existing.get(lc, {}).get(endpoint, set())
            new_ids = covered_ids - already_covered

            for fid in new_ids:
                comp_rows.append({
                    "league_code": lc,
                    "fixture_id":  fid,
                    "endpoint":    endpoint,
                })

            print(f"  [{lc}] {entity}: {len(covered_ids)} in raw, {len(already_covered)} already covered, {len(new_ids)} new")

        all_coverage_rows.extend(comp_rows)
        totals[lc] = len(comp_rows)
        print(f"  [{lc}] new coverage rows: {len(comp_rows)}\n")

    print(f"Writing {len(all_coverage_rows):,} new coverage rows to {_coverage_table_id()} ...")
    if all_coverage_rows:
        write_coverage(client, all_coverage_rows)
        print("Done.")
    else:
        print("Nothing to write — all fixtures already covered.")

    print("\nSummary:")
    for lc in sorted(totals):
        print(f"  {lc}: {totals[lc]} new rows")
    print(f"\nTotal: {len(all_coverage_rows):,} new coverage rows written.")


if __name__ == "__main__":
    main()
