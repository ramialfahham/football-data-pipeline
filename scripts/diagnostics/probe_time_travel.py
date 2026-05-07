"""Probe a raw table at past timestamps via BigQuery time travel.

For each timestamp, prints the table's payload state (ingested_at,
$.response.length) at that moment. Used to find the latest pre-corruption
snapshot before triggering a restore.

BigQuery time travel keeps prior table state for up to 7 days by default.
Probes default to 1 hour, 6 hours, 12 hours, 1 day, 2 days, 4 days, and
6.5 days ago. Override with --hours-ago.

Usage:
    python scripts/diagnostics/probe_time_travel.py --table RAW_APIF_BL1_LEAGUES
    python scripts/diagnostics/probe_time_travel.py --table RAW_APIF_BL1_LEAGUES \\
        --hours-ago 1 6 24
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from google.cloud import bigquery

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"

DEFAULT_HOURS_AGO = [1, 6, 12, 24, 48, 96, 156]  # 156h = 6.5 days


def probe(client: bigquery.Client, table_id: str, ts_utc: datetime) -> None:
    iso = ts_utc.strftime("%Y-%m-%d %H:%M:%S")
    sql = (
        f"select ingested_at, to_json_string(payload) as payload_json "
        f"from `{table_id}` for system_time as of timestamp('{iso} UTC') "
        "order by ingested_at desc limit 1"
    )
    print(f"--- AS OF {iso} UTC")
    try:
        rows = list(client.query(sql).result())
    except Exception as e:
        print(f"  query failed: {e}")
        print()
        return
    if not rows:
        print("  no rows at this timestamp")
        print()
        return
    row = rows[0]
    payload = json.loads(row.payload_json)
    response = payload.get("response")
    results = payload.get("results")
    errors = payload.get("errors")
    print(f"  ingested_at: {row.ingested_at}")
    print(f"  $.results:   {results!r}")
    resp_len = len(response) if hasattr(response, "__len__") else "N/A"
    print(f"  $.response:  {type(response).__name__}, len={resp_len}")
    if isinstance(response, list) and response:
        print("  -> RECOVERABLE ✓")
    else:
        print(f"  $.errors:    {errors!r}")
        print("  -> empty / corrupt at this timestamp")
    print()


def main(table: str, hours_ago: list[int]) -> None:
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{table}"
    now = datetime.now(timezone.utc)
    print(f"Probing {table_id} at past timestamps (BigQuery time travel limit = 7 days)")
    print()
    for hours in sorted(hours_ago):
        probe(client, table_id, now - timedelta(hours=hours))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--table", required=True, help="Raw table name, e.g. RAW_APIF_BL1_LEAGUES")
    parser.add_argument(
        "--hours-ago",
        type=int,
        nargs="+",
        default=DEFAULT_HOURS_AGO,
        help=f"Hours-ago points to probe. Default: {DEFAULT_HOURS_AGO}",
    )
    args = parser.parse_args()
    main(args.table, args.hours_ago)
