"""Verify match-preview metric_manifest ids exist in site i18n metrics namespace."""
from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "site" / "match-preview" / "metric_manifest.json"
I18N_DIR = REPO_ROOT / "site" / "i18n"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    metric_ids = [m["metric_id"] for m in manifest.get("metrics", [])]
    if not metric_ids:
        print("check_ui_i18n_metrics: no metrics in manifest", file=sys.stderr)
        return 1

    errors: list[str] = []
    for lang_path in sorted(I18N_DIR.glob("*.json")):
        lang = lang_path.stem
        data = json.loads(lang_path.read_text(encoding="utf-8"))
        metrics_ns = data.get("metrics") or {}
        for mid in metric_ids:
            entry = metrics_ns.get(mid)
            if not entry:
                errors.append(f"{lang}: missing metrics.{mid}")
                continue
            if not entry.get("label"):
                errors.append(f"{lang}: metrics.{mid}.label is empty")
            if not entry.get("description"):
                errors.append(f"{lang}: metrics.{mid}.description is empty")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"OK: {len(metric_ids)} manifest metrics present in {len(list(I18N_DIR.glob('*.json')))} i18n file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
