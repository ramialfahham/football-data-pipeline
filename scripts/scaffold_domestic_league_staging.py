#!/usr/bin/env python3
"""Scaffold staging models from BL1. Usage: python scripts/scaffold_domestic_league_staging.py CODE folder"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BL1_DIR = REPO / "dbt_project" / "models" / "1_staging" / "api_football" / "bl1"
STAGING_ROOT = REPO / "dbt_project" / "models" / "1_staging" / "api_football"


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: scaffold_domestic_league_staging.py LEAGUE_CODE folder")
        return 1
    league_code = sys.argv[1].upper()
    folder = sys.argv[2].lower()
    target = STAGING_ROOT / folder
    target.mkdir(parents=True, exist_ok=True)
    for src_path in sorted(BL1_DIR.glob("stg_apif__bl1_*.sql")):
        entity = src_path.stem.replace("stg_apif__bl1_", "")
        text = src_path.read_text(encoding="utf-8")
        text = text.replace("'BL1'", f"'{league_code}'")
        text = text.replace("BL1", league_code)
        text = text.replace("bl1", folder)
        (target / f"stg_apif__{folder}_{entity}.sql").write_text(text, encoding="utf-8")
    print(f"Wrote staging for {league_code} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
