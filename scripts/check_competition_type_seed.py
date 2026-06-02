"""Verify every competition_type used in the registry has a row in the competition_types seed.

The seed dbt_project/seeds/competition_types.csv is the single source of truth for the
club/national split (entity_type). Downstream models look up entity_type by
competition_type, so a competition referencing a type that is not in the seed would get
no club/national classification. This check fails CI if that ever happens.

Registry source of truth: docs/competition_registry.yml (any status).
Seed: dbt_project/seeds/competition_types.csv.

Usage (from repo root or dbt_project/):
    python scripts/check_competition_type_seed.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "competition_registry.yml"
SEED_PATH = REPO_ROOT / "dbt_project" / "seeds" / "competition_types.csv"


def _registry_competition_types() -> set[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: set[str] = set()
    for row in comps:
        if not isinstance(row, dict):
            continue
        ct = row.get("competition_type")
        if ct:
            out.add(str(ct))
    return out


def _seed_competition_types() -> set[str]:
    with SEED_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "competition_type" not in (reader.fieldnames or []):
            raise KeyError(
                f"{SEED_PATH.name} missing required column 'competition_type'"
            )
        return {row["competition_type"].strip() for row in reader if row.get("competition_type")}


def main() -> int:
    try:
        reg_types = _registry_competition_types()
        seed_types = _seed_competition_types()
    except Exception as e:
        print(f"check_competition_type_seed: {e}", file=sys.stderr)
        return 1

    if not reg_types:
        print(
            "check_competition_type_seed: registry has no competition_type values",
            file=sys.stderr,
        )
        return 1

    missing = sorted(reg_types - seed_types)
    if missing:
        print(
            "check_competition_type_seed: competition_type(s) used in the registry but "
            f"absent from competition_types.csv: {missing}. Add a row (with entity_type "
            "club|national) to dbt_project/seeds/competition_types.csv.",
            file=sys.stderr,
        )
        return 1

    print(
        f"check_competition_type_seed: OK ({len(reg_types)} registry type(s) all present "
        f"in seed of {len(seed_types)})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
