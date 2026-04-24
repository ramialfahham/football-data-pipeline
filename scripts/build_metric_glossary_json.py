#!/usr/bin/env python3
"""Build artifacts/metric_glossary.json from dbt_project/seeds/metric_glossary.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=root / "dbt_project" / "seeds" / "metric_glossary.csv",
    )
    parser.add_argument(
        "out_path",
        nargs="?",
        type=Path,
        default=root / "artifacts" / "metric_glossary.json",
    )
    args = parser.parse_args()
    src: Path = args.csv_path
    dst: Path = args.out_path

    rows: list[dict[str, str]] = []
    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected = {"metric_key", "label", "description"}
        if reader.fieldnames is None or not expected.issubset(set(reader.fieldnames)):
            raise SystemExit(
                f"{src}: expected columns {sorted(expected)}, got {reader.fieldnames!r}"
            )
        for row in reader:
            key = (row.get("metric_key") or "").strip()
            if not key or key.startswith("#"):
                continue
            rows.append(
                {
                    "metric_key": key,
                    "label": (row.get("label") or "").strip(),
                    "description": (row.get("description") or "").strip(),
                }
            )

    dst.parent.mkdir(parents=True, exist_ok=True)
    payload = {"metrics": rows}
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} metrics to {dst}")


if __name__ == "__main__":
    main()
