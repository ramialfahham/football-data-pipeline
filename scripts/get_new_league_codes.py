"""Print comma-separated league codes that need CI bootstrap ingestion.

A league needs bootstrap if its league_code does not yet appear in the unified
RAW_APIF_FIXTURES_NEXT table. Reads active + ingest_active competitions from the
registry, queries BigQuery for existing league_codes, and outputs only the missing ones.

Usage (from repo root, with GCP credentials active):
    python scripts/get_new_league_codes.py

Output examples:
    PL,ED,SPL        <- leagues not yet in RAW_APIF_FIXTURES_NEXT
    (empty string)   <- all leagues already present; skip ingest

Used by ci-data-build.yml to set API_FOOTBALL_LEAGUE_CODES for the bootstrap step.
Exit code 0 always (empty output = nothing to do, not an error).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "competition_registry.yml"
GCP_PROJECT_ID = "football-data-pipeline-gcp"
DATASET_ID = "raw"
UNIFIED_TABLE = f"{GCP_PROJECT_ID}.{DATASET_ID}.RAW_APIF_FIXTURES_NEXT"


def _active_ingest_codes() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: list[str] = []
    for row in comps:
        if not isinstance(row, dict):
            continue
        if row.get("status") not in ("active", "in_progress"):
            continue
        if not row.get("ingest_active", True):
            continue
        code = row.get("league_code")
        if code:
            out.append(str(code))
    return out


def _existing_codes(client) -> set[str]:
    query = f"SELECT DISTINCT league_code FROM `{UNIFIED_TABLE}`"
    result = client.query(query).result()
    return {row.league_code for row in result}


def main() -> int:
    try:
        from google.cloud import bigquery
    except ImportError:
        print(
            "get_new_league_codes: google-cloud-bigquery not installed", file=sys.stderr
        )
        return 1

    try:
        codes = _active_ingest_codes()
    except Exception as e:
        print(f"get_new_league_codes: failed to read registry — {e}", file=sys.stderr)
        return 1

    client = bigquery.Client(project=GCP_PROJECT_ID)
    existing = _existing_codes(client)
    new_codes = [c for c in codes if c not in existing]

    if new_codes:
        print(",".join(new_codes))
    else:
        print("", end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
