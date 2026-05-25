"""One-time migration: seed RAW_APIF_FIXTURE_COVERAGE from existing fanout blob data.

WHY THIS SCRIPT EXISTS
----------------------
Issue #221 introduces RAW_APIF_FIXTURE_COVERAGE — a tracking table that records
which (league_code, fixture_id, endpoint) combinations have already been fetched.
The fanout pipeline now reads this table at startup instead of parsing merged JSON
blobs to determine what is already covered.

Without this migration, the coverage table starts empty. The first pipeline run
after deploying #221 would see every fixture as uncovered and re-fetch all five
endpoints for every historical fixture — burning the entire daily API quota on
work that has already been done.

This script reads the existing fanout blob data (the last row in each raw fanout
table, written by the old merge-on-write pipeline), extracts fixture IDs, and
writes the corresponding coverage rows into RAW_APIF_FIXTURE_COVERAGE. After this
script runs, daily fanout runs only fetch genuinely missing data.

WHAT THIS SCRIPT DOES
---------------------
For each active competition in the registry and each of the five fanout endpoints:

  1. Read the latest raw payload from the raw fanout table (e.g.
     RAW_APIF_BL1_LINEUPS). This is the merged blob written by the old pipeline —
     it contains one response entry per covered fixture.
  2. Extract fixture IDs from the response. For FIXTURE_STATISTICS, only count
     entries where the statistics list is non-empty (matching the rule used by
     the new pipeline when writing coverage).
  3. Collect coverage rows: (league_code, fixture_id, endpoint) for each covered
     fixture.

All coverage rows are written to RAW_APIF_FIXTURE_COVERAGE in one batch at the end.

WHAT THIS SCRIPT DOES NOT DO
-----------------------------
- It does not modify the fanout raw tables.
- It is idempotent in the sense that it reads existing data and produces the same
  coverage rows on every run (though writing duplicates is harmless — the
  pipeline's gap-detection reads the coverage table and deduplicates by presence).
- It does not touch dbt, staging, or any other layer.

HOW TO RUN
----------
From the repository root:

    python scripts/populate_coverage_table.py

Requires the standard GCP authentication environment
(GOOGLE_APPLICATION_CREDENTIALS or application default credentials).
Run once, before deploying the #221 pipeline changes.
"""

from __future__ import annotations

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


def _read_latest_fanout_blob(client: bigquery.Client, table_id: str) -> dict | None:
    """Read the most recent row's payload from a fanout raw table.

    Delegates to the package's read_latest_payload_json which correctly
    handles both string and pre-parsed dict payloads from the BQ client.
    Returns None if the table does not exist or has no rows.
    """
    # Import here so the script can be run from the repo root via sys.path.
    from ingestion.api_football.bigquery import read_latest_payload_json

    # Strip the project.dataset prefix — read_latest_payload_json expects
    # just the table name (e.g. RAW_APIF_BL1_LINEUPS).
    table_name = table_id.split(".")[-1]
    try:
        return read_latest_payload_json(client, table_name)
    except Exception as e:
        print(f"  WARNING: read failed for {table_id}: {e}", file=sys.stderr)
        return None


def _extract_covered_fixture_ids(
    payload: dict | None,
    *,
    required_payload_key: str | None,
) -> set[int]:
    """Extract fixture IDs from a fanout blob response.

    When required_payload_key is given (only for FIXTURE_STATISTICS), a fixture
    is only counted as covered if its payload list for that key is non-empty.
    This matches the rule applied by the new pipeline when writing coverage rows.
    """
    out: set[int] = set()
    for row in (payload or {}).get("response") or []:
        fid = row.get("fixture_id")
        if fid is None:
            continue
        if required_payload_key is not None:
            if not row.get(required_payload_key):
                continue
        try:
            out.add(int(fid))
        except (TypeError, ValueError):
            continue
    return out


def _table_exists(client: bigquery.Client, table_id: str) -> bool:
    try:
        client.get_table(table_id)
        return True
    except Exception:
        return False


def main() -> None:
    # Import here so the script works even when run outside the package.
    import sys
    sys.path.insert(0, ".")
    from ingestion.api_football.registry import selected_competitions
    from ingestion.api_football.coverage import ensure_coverage_table, write_coverage

    client = bigquery.Client(project=GCP_PROJECT)

    # Ensure the coverage table exists before writing.
    ensure_coverage_table(client)

    # Check if the coverage table already has rows — in that case, warn the user
    # rather than silently writing duplicates. The pipeline handles duplicates
    # gracefully (coverage rows are only written for genuinely missing fixtures),
    # but a second run of this script is usually not needed.
    coverage_table_id = _coverage_table_id()
    if _table_exists(client, coverage_table_id):
        q = f"SELECT COUNT(*) AS n FROM `{coverage_table_id}`"
        rows = list(client.query(q).result())
        existing_count = rows[0].n if rows else 0
        if existing_count > 0:
            print(
                f"RAW_APIF_FIXTURE_COVERAGE already has {existing_count:,} rows. "
                "Re-running will add duplicate records for already-covered fixtures, "
                "which is harmless but unnecessary. Press Ctrl-C to abort, or wait 5s to continue."
            )
            import time
            time.sleep(5)

    selected, skipped = selected_competitions()
    print(f"Processing {len(selected)} active competitions...\n")

    all_coverage_rows: list[dict] = []
    totals: dict[str, int] = {}

    for comp in selected:
        lc = comp.league_code
        comp_rows: list[dict] = []

        for entity, endpoint in ENTITY_TO_ENDPOINT.items():
            table_id = _raw_table_id(lc, entity)
            payload = _read_latest_fanout_blob(client, table_id)
            if payload is None:
                print(f"  [{lc}] {entity}: table missing or empty — skipped")
                continue

            required_key = ENTITY_TO_PAYLOAD_KEY[entity]
            covered_ids = _extract_covered_fixture_ids(payload, required_payload_key=required_key)

            for fid in covered_ids:
                comp_rows.append({
                    "league_code": lc,
                    "fixture_id":  fid,
                    "endpoint":    endpoint,
                })

            print(f"  [{lc}] {entity}: {len(covered_ids)} fixture IDs covered")

        all_coverage_rows.extend(comp_rows)
        totals[lc] = len(comp_rows)
        print(f"  [{lc}] total coverage rows: {len(comp_rows)}\n")

    print(f"Writing {len(all_coverage_rows):,} coverage rows to {coverage_table_id} ...")
    if all_coverage_rows:
        write_coverage(client, all_coverage_rows)
        print("Done.")
    else:
        print("No coverage rows to write — all fanout tables were empty or missing.")

    print("\nSummary:")
    for lc in sorted(totals):
        print(f"  {lc}: {totals[lc]} rows")
    print(f"\nTotal: {len(all_coverage_rows):,} coverage rows written.")
    print(
        "\nNext step: deploy the #221 pipeline changes. The first daily run will "
        "only fetch genuinely missing fixture-endpoint combinations."
    )


if __name__ == "__main__":
    main()
