"""Drop every RAW_APIF_*_INJURIES table from BigQuery.

⚠ THIS SCRIPT HAS OUTLIVED ONE REMOVAL ALREADY. It was written for `401c1cc` (2026-05-10), which
removed the injuries surface because it had no consumer. The endpoint was re-added sixteen days
later (`983d12c`) with no consumer named, migrated to the unified raw tables (`178261d`), and ran
for three months writing `RAW_APIF_INJURIES` — 1.975 GiB, the largest raw table — that nothing
ever read. #33 item 15 removes it again. If a third re-add is ever proposed, read
`.claude/task/escalations.log` for why the first two failed to justify themselves.

The match pattern is unchanged and still correct: it targets tables whose name starts with
``RAW_APIF_`` and ends with ``_INJURIES``. That covered the retired per-competition naming
(``RAW_APIF_BL1_INJURIES``) and still covers the unified ``RAW_APIF_INJURIES``, since that also
ends in ``_INJURIES``. Non-injury tables are never listed.

⚠ IRREVERSIBLE past BigQuery's 7-day time travel. Run `--dry-run` first and have the printed list
confirmed before the real run. Run it only AFTER the ingest removal has merged and the nightly
image has been redeployed — otherwise the next run recreates the table.

Usage:
    python scripts/drop_injuries_raw_tables.py --dry-run
    python scripts/drop_injuries_raw_tables.py
"""

from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"
PREFIX = "RAW_APIF_"
SUFFIX = "_INJURIES"


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    dataset_ref = f"{PROJECT}.{DATASET}"
    try:
        tables = list(client.list_tables(dataset_ref))
    except NotFound:
        print(f"Dataset {dataset_ref} not found.")
        sys.exit(1)

    targets = sorted(
        t.table_id for t in tables
        if t.table_id.startswith(PREFIX) and t.table_id.endswith(SUFFIX)
    )

    if not targets:
        print("No RAW_APIF_*_INJURIES tables found. Nothing to drop.")
        return

    print(f"Found {len(targets)} injury raw table(s) to drop:")
    for name in targets:
        print(f"  - {name}")
    print()

    dropped = 0
    errors: list[str] = []
    for name in targets:
        full_id = f"{PROJECT}.{DATASET}.{name}"
        if dry_run:
            print(f"  would drop {name}")
            continue
        try:
            client.delete_table(full_id)
            print(f"  dropped {name}")
            dropped += 1
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  FAIL {name}: {e}", file=sys.stderr)

    if dry_run:
        print(f"\nDry run: {len(targets)} table(s) would be dropped.")
    else:
        print(f"\nDropped {dropped} of {len(targets)} table(s).")

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
