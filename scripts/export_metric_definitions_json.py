#!/usr/bin/env python3
"""Export dbt seed metric_definitions.csv to site JSON for static UI binding."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=root / "dbt_project" / "seeds" / "metric_definitions.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=root / "site" / "match-preview" / "metric_definitions.json",
    )
    args = parser.parse_args()

    defs: dict[str, dict[str, str | bool]] = {}
    with args.csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = (row.get("metric_id") or "").strip()
            if not mid:
                continue
            entry: dict[str, str | bool] = {
                "format": (row.get("format") or "").strip(),
                "context": (row.get("context") or "").strip(),
            }
            if (row.get("lower_is_better") or "").strip().lower() in ("true", "1", "yes"):
                entry["lower_is_better"] = True
            for col in ("home_column", "away_column", "single_column"):
                val = (row.get(col) or "").strip()
                if val:
                    entry[col] = val
            defs[mid] = entry

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(defs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(defs)} metric definitions to {args.out}")


if __name__ == "__main__":
    main()
