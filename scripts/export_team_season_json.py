"""Export BL1 team-season insights JSON (legacy single-file entry point).

Prefer `python scripts/export_pages_data.py` for all domestic leagues and the
Pages manifest. This script exports BL1 only to the path you pass.

Usage:
    python scripts/export_team_season_json.py <output_path>
"""
from __future__ import annotations

import pathlib
import sys

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from export_pages_data import fetch_team_season_rows, write_json


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: export_team_season_json.py <output_path>")
        return 1

    output_path = pathlib.Path(sys.argv[1])
    try:
        from google.cloud import bigquery
    except ImportError:
        print("google-cloud-bigquery is not installed. Run: pip install -r requirements.txt")
        return 1

    from export_pages_data import GCP_PROJECT

    client = bigquery.Client(project=GCP_PROJECT)
    rows = fetch_team_season_rows(client, "BL1")
    write_json(output_path, {"teams": rows})
    print(f"Wrote {output_path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
