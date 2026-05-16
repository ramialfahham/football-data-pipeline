"""Compare live API-Football fixture statistics vs latest raw merged payload."""

from __future__ import annotations

import argparse
import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from google.cloud import bigquery

from ingestion.api_football.http_client import fetch_json
from ingestion.api_football.settings import GCP_PROJECT_ID, get_headers, raw_league_table
from ingestion.api_football.bigquery import read_latest_payload_json


def _stats_nonempty(block: dict) -> bool:
    stats = block.get("statistics")
    return isinstance(stats, list) and len(stats) > 0


def _raw_block_for_fixture(payload: dict | None, fixture_id: int) -> dict | None:
    for row in (payload or {}).get("response") or []:
        if int(row.get("fixture_id", -1)) == fixture_id:
            return row
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("league_code", help="Internal league code, e.g. WCQAF")
    parser.add_argument("fixture_ids", nargs="+", type=int, help="Fixture id(s) to compare")
    args = parser.parse_args()

    client = bigquery.Client(project=GCP_PROJECT_ID)
    tbl = raw_league_table(args.league_code, "FIXTURE_STATISTICS")
    prior = read_latest_payload_json(client, tbl)
    headers = get_headers()

    for fixture_id in args.fixture_ids:
        live = fetch_json(
            "/fixtures/statistics",
            headers=headers,
            params={"fixture": fixture_id},
        )
        raw_row = _raw_block_for_fixture(prior, fixture_id)
        print(f"\n=== {args.league_code} fixture {fixture_id} ===")
        print(
            "live_nonempty:",
            _stats_nonempty({"statistics": live.get("response", [])}),
            "results:",
            live.get("results"),
        )
        if live.get("errors"):
            print("live_errors:", json.dumps(live["errors"], indent=2))
        if raw_row is None:
            print("raw: no block for fixture_id")
        else:
            print("raw_nonempty:", _stats_nonempty(raw_row))
            if not _stats_nonempty(raw_row) and _stats_nonempty(
                {"statistics": live.get("response", [])}
            ):
                print("MISMATCH: API has stats but raw block is empty")


if __name__ == "__main__":
    main()
