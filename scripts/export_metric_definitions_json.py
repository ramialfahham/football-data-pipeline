#!/usr/bin/env python3
"""Export the live match-preview metric-definitions JSON for static UI binding.

Composes two sources (the catalogue is never modified here):
  - metric_catalogue.csv  — the single source of truth for each metric. This script reads
    `format`, `direction` (exported as `lower_is_better`) and `label_i18n_key` from it.
  - metric_bindings.csv   — the live display wiring: each windowed live id, the catalogue
    metric it maps to, the JSON columns that feed it, and the render context.

Output (site/match-preview/metric_definitions.json) is consumed by the static match-preview
UI. It must stay byte-identical unless a binding or definition deliberately changes; the test
`tests/test_metric_bindings.py` regenerates and asserts equality against the committed file.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_catalogue(path: Path) -> dict[tuple[str, str], dict[str, object]]:
    """(metric_id, entity) -> definition; a metric can have both a team and a player row."""
    catalogue: dict[tuple[str, str], dict[str, object]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = (row.get("metric_id") or "").strip()
            entity = (row.get("entity") or "").strip().lower()
            if not mid:
                continue
            catalogue[(mid, entity)] = {
                "format": (row.get("format") or "").strip(),
                "lower_is_better": (row.get("direction") or "").strip() == "lower_better",
                "label_i18n_key": (row.get("label_i18n_key") or "").strip(),
            }
    return catalogue


def build_defs(bindings_path: Path, catalogue_path: Path) -> dict[str, dict[str, object]]:
    """Compose the per-live-id binding dict; a pair missing from the catalogue is a hard error."""
    catalogue = load_catalogue(catalogue_path)
    defs: dict[str, dict[str, object]] = {}
    with bindings_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            live_id = (row.get("live_id") or "").strip()
            if not live_id:
                continue
            cat_id = (row.get("catalogue_metric_id") or "").strip()
            cat_entity = (row.get("catalogue_entity") or "").strip().lower()
            cat_row = catalogue.get((cat_id, cat_entity))
            if cat_row is None:
                raise SystemExit(
                    f"metric_bindings: '{live_id}' references unknown catalogue metric "
                    f"'{cat_id}' for entity '{cat_entity}'"
                )
            entry: dict[str, object] = {}
            if cat_row["label_i18n_key"]:
                entry["label"] = cat_row["label_i18n_key"]
            entry["format"] = cat_row["format"]
            entry["context"] = (row.get("context") or "").strip()
            if cat_row["lower_is_better"]:
                entry["lower_is_better"] = True
            for col in ("home_column", "away_column", "single_column"):
                val = (row.get(col) or "").strip()
                if val:
                    entry[col] = val
            defs[live_id] = entry
    return defs


def render(defs: dict[str, dict[str, object]]) -> str:
    return json.dumps(defs, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bindings",
        type=Path,
        default=root / "site" / "match-preview" / "metric_bindings.csv",
    )
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=root / "dbt_project" / "seeds" / "metric_catalogue.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=root / "site" / "match-preview" / "metric_definitions.json",
    )
    args = parser.parse_args()

    defs = build_defs(args.bindings, args.catalogue)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(defs), encoding="utf-8")
    print(f"Wrote {len(defs)} metric definitions to {args.out}")


if __name__ == "__main__":
    main()
