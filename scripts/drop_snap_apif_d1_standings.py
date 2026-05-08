"""Drop the orphaned snap_apif_d1_standings table after the snapshot was removed.

The dbt snapshot is replaced by base_apif__bl1_standings (one row per
(league_code, season, team_id) deduplicated from staging). The snapshot's
SCD2 history was never consumed downstream, and its (league_code, season,
team_id, group_description) unique_key caused stale-zone rows to leak into
fct_standings — see PR #51 for the mart-level workaround and the snapshot
removal PR for the structural fix.

Run once after the snapshot removal merges. dbt will not recreate the
table because the snapshot definition no longer exists.

Usage:
    python scripts/drop_snap_apif_d1_standings.py [--dry-run]
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
