"""Verify every metric_manifest.json metric_id has a row in the metric_catalogue seed."""
from __future__ import annotations

import csv
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "site" / "match-preview" / "metric_manifest.json"
CATALOGUE = REPO_ROOT / "dbt_project" / "seeds" / "metric_catalogue.csv"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_ids = [m["metric_id"] for m in manifest.get("metrics", [])]
    if not manifest_ids:
        print("check_metric_catalogue: no metrics found in manifest", file=sys.stderr)
        return 1

    with CATALOGUE.open(encoding="utf-8", newline="") as fh:
        catalogue_ids = {row["metric_id"] for row in csv.DictReader(fh)}

    missing = [mid for mid in manifest_ids if mid not in catalogue_ids]
    if missing:
        for mid in missing:
            print(
                f"metric_manifest.json metric '{mid}' has no row in metric_catalogue.csv",
                file=sys.stderr,
            )
        return 1

    print(
        f"OK: all {len(manifest_ids)} manifest metrics are defined in metric_catalogue.csv"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
