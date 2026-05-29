"""Purge stale RAW_APIF_FIXTURE_DETAILS rows whose competition ID no longer matches the registry.

Background
----------
RAW_APIF_FIXTURE_DETAILS is WRITE_APPEND. When a competition's provider_league_id
is corrected (e.g. PR #296 fixed GCUP 8 -> 22, CNL 43 -> 536, CDR 556 -> 143,
DFBP 529 -> 81), the next ingest writes correct rows under the SAME league_code,
but the previously-written rows — carrying the wrong competition's teams and
fixtures inside their payload — are left orphaned in the table.

Those orphaned rows fail the dim_team relationship tests, because their teams
(e.g. FIFA Women's World Cup national teams written under league_code='GCUP')
legitimately do not exist in the corrected competition's fixtures/teams data.

This script reconciles the table against the registry: for every competition with
a known provider_league_id, any fixture-details row whose payload $.league.id is
NOT that ID is stale and is deleted. It is registry-driven and competition-agnostic
— it self-heals any future ID correction, not just the four known cases.

Usage
-----
    python scripts/diagnostics/purge_stale_fixture_details.py [--dry-run]

Options
-------
    --dry-run   Report stale-row counts per competition without deleting.

Safety
------
    - Only deletes rows where $.league.id differs from the registry ID — correct
      rows are never touched.
    - Competitions with a null provider_league_id are skipped (nothing to reconcile).
    - Idempotent: re-running after a clean purge reports 0 stale rows.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from google.cloud import bigquery

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from ingestion.api_football.settings import GCP_PROJECT_ID, DATASET_ID, raw_table  # noqa: E402


def _table_id() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('FIXTURE_DETAILS')}"


def _registry_ids() -> dict[str, int]:
    """Map league_code -> provider_league_id for entries that have an ID."""
    path = _ROOT / "docs" / "competition_registry.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for entry in data["competitions"]:
        lid = entry.get("provider_league_id")
        if lid is not None:
            out[entry["league_code"]] = int(lid)
    return out


def _stale_counts(client: bigquery.Client, table: str, ids: dict[str, int]) -> list[tuple[str, int, int, int]]:
    """Return [(league_code, expected_id, stale_api_id, stale_rows), ...] for mismatches."""
    q = f"""
        SELECT
          league_code,
          SAFE_CAST(JSON_VALUE(payload, '$.league.id') AS INT64) AS payload_league_id,
          COUNT(*) AS n
        FROM `{table}`
        GROUP BY 1, 2
        ORDER BY league_code, n DESC
    """
    rows = list(client.query(q).result())
    stale: list[tuple[str, int, int, int]] = []
    for r in rows:
        expected = ids.get(r.league_code)
        if expected is None:
            continue  # competition not in registry / no ID — skip
        if r.payload_league_id != expected:
            stale.append((r.league_code, expected, r.payload_league_id, int(r.n)))
    return stale


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Purge stale RAW_APIF_FIXTURE_DETAILS rows that no longer match the registry ID.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report stale-row counts without deleting.",
    )
    args = parser.parse_args()

    client = bigquery.Client(project=GCP_PROJECT_ID)
    table = _table_id()
    ids = _registry_ids()

    print(f"\nTarget table: {table}")
    print(f"Registry competitions with provider_league_id: {len(ids)}")

    stale = _stale_counts(client, table, ids)

    if not stale:
        print("\nNo stale rows — every fixture-details row matches its registry provider_league_id.")
        return

    total_stale = sum(n for _, _, _, n in stale)
    print(f"\nStale rows found ({total_stale:,} total across {len(stale)} mismatch group(s)):")
    print("-" * 80)
    for lc, expected, got, n in stale:
        print(f"  {lc:<8}  expected league.id={expected:<6}  stale league.id={got!s:<8}  rows={n:,}")
    print("-" * 80)

    if args.dry_run:
        print("\n[DRY RUN] Not deleting. Re-run without --dry-run to purge.")
        return

    # Delete per (league_code, expected_id): remove any row whose payload league.id
    # is not the registry ID for that league_code.
    print("\nDeleting stale rows …")
    affected_codes = sorted({lc for lc, _, _, _ in stale})
    total_deleted = 0
    for lc in affected_codes:
        expected = ids[lc]
        delete_sql = f"""
            DELETE FROM `{table}`
            WHERE league_code = '{lc}'
              AND SAFE_CAST(JSON_VALUE(payload, '$.league.id') AS INT64) != {expected}
        """
        job = client.query(delete_sql)
        job.result()
        deleted = job.num_dml_affected_rows or 0
        total_deleted += deleted
        print(f"  {lc:<8}  deleted {deleted:,} stale row(s) (kept league.id={expected})")

    print(f"\nPurge complete. Total rows deleted: {total_deleted:,}")

    remaining = _stale_counts(client, table, ids)
    if not remaining:
        print("Verification: 0 stale rows remain — table is reconciled with the registry.")
    else:
        rem_total = sum(n for _, _, _, n in remaining)
        print(f"WARNING: {rem_total:,} stale row(s) still present. Investigate.")


if __name__ == "__main__":
    main()
