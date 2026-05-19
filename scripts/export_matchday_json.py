"""Export BL1 matchday insights JSON (legacy single-file entry point).

Prefer `python scripts/export_pages_data.py` for all domestic leagues and the
Pages manifest. Queries mart_matchday_insights with league_code = BL1, or the
relegation mart when that slice is empty.

Usage:
    python scripts/export_matchday_json.py <output_path>
"""
from __future__ import annotations

import pathlib
import sys

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from export_pages_data import domestic_league_codes, fetch_matchday_rows, write_json


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: export_matchday_json.py <output_path>")
        return 1

    if "BL1" not in domestic_league_codes():
        print("export_matchday_json: BL1 is not in domestic export list", file=sys.stderr)
        return 1

    output_path = pathlib.Path(sys.argv[1])
    try:
        from google.cloud import bigquery
    except ImportError:
        print("google-cloud-bigquery is not installed. Run: pip install -r requirements.txt")
        return 1

    from export_pages_data import GCP_PROJECT

    client = bigquery.Client(project=GCP_PROJECT)
    rows, source_mart = fetch_matchday_rows(client, "BL1")
    write_json(output_path, {"show": rows})
    print(f"Wrote {output_path} ({len(rows)} rows, source_mart={source_mart})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
