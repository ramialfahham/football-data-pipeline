"""Verify each shown match-preview metric resolves to an i18n label under its official key.

The match-preview manifest lists windowed live ids; each maps (via metric_bindings.csv) to its
official catalogue id, which is the i18n key standardized in #500 (metrics.<official_id>.label).
This checks every shown stat has a non-empty label + description in every site/i18n/*.json.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "site" / "match-preview" / "metric_manifest.json"
BINDINGS = REPO_ROOT / "site" / "match-preview" / "metric_bindings.csv"
I18N_DIR = REPO_ROOT / "site" / "i18n"


def _live_to_official() -> dict[str, str]:
    mapping: dict[str, str] = {}
    with BINDINGS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            live = (row.get("live_id") or "").strip()
            if live:
                mapping[live] = (row.get("catalogue_metric_id") or "").strip()
    return mapping


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    live_ids = [m["metric_id"] for m in manifest.get("metrics", [])]
    if not live_ids:
        print("check_ui_i18n_metrics: no metrics in manifest", file=sys.stderr)
        return 1

    mapping = _live_to_official()
    errors: list[str] = []
    official_ids: list[str] = []
    for live in live_ids:
        official = mapping.get(live)
        if not official:
            errors.append(f"manifest metric '{live}' has no binding in metric_bindings.csv")
            continue
        official_ids.append(official)

    for lang_path in sorted(I18N_DIR.glob("*.json")):
        lang = lang_path.stem
        data = json.loads(lang_path.read_text(encoding="utf-8"))
        metrics_ns = data.get("metrics") or {}
        for oid in official_ids:
            entry = metrics_ns.get(oid)
            if not entry:
                errors.append(f"{lang}: missing metrics.{oid}")
                continue
            if not entry.get("label"):
                errors.append(f"{lang}: metrics.{oid}.label is empty")
            if not entry.get("description"):
                errors.append(f"{lang}: metrics.{oid}.description is empty")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(
        f"OK: {len(official_ids)} shown metrics resolve to i18n labels "
        f"in {len(list(I18N_DIR.glob('*.json')))} file(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
