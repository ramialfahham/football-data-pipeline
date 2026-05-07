"""Restore a raw table from a BigQuery time-travel snapshot.

Reads the table state as of a chosen past timestamp, validates that the
payload has a non-empty $.response, and writes it back to the live table
via WRITE_TRUNCATE. The original ingested_at is preserved so the audit
trail still reflects when the data was actually fetched from the API.

Use after probe_time_travel.py has identified a pre-corruption timestamp
that holds valid data. Default is dry-run; pass --apply to commit.

Usage:
    # dry-run: show what would be restored, change nothing
    python scripts/diagnostics/restore_from_time_travel.py \\
        --table RAW_APIF_BL1_LEAGUES \\
        --timestamp '2026-05-07 17:55:00'

    # apply: actually overwrite the live table
    python scripts/diagnostics/restore_from_time_travel.py \\
        --table RAW_APIF_BL1_LEAGUES \\
        --timestamp '2026-05-07 17:55:00' \\
        --apply
"""

from __future__ import annotations

import argparse
import io
import json

from google.cloud import bigquery

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"


def fetch_snapshot(client: bigquery.Client, table_id: str, ts_utc: str) -> tuple[dict, str]:
    sql = (
        f"select ingested_at, to_json_string(payload) as payload_json "
        f"from `{table_id}` for system_time as of timestamp('{ts_utc} UTC') "
        "order by ingested_at desc limit 1"
    )
    rows = list(client.query(sql).result())
    if not rows:
        raise RuntimeError(f"time travel at {ts_utc} UTC returned no rows for {table_id}")
    row = rows[0]
    payload = json.loads(row.payload_json)
    if not payload.get("response"):
        raise RuntimeError(
            f"time travel at {ts_utc} UTC returned empty response for {table_id} — "
            "wrong timestamp, or this snapshot is also corrupt"
        )
    return payload, row.ingested_at.isoformat()


def write_back(client: bigquery.Client, table_id: str, payload: dict, ingested_at_iso: str) -> None:
    line = json.dumps(
        {"payload": payload, "ingested_at": ingested_at_iso},
        ensure_ascii=True,
    ) + "\n"
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("payload", "JSON"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP"),
        ],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_TRUNCATE",
    )
    job = client.load_table_from_file(
        io.BytesIO(line.encode("utf-8")),
        table_id,
        job_config=job_config,
    )
    job.result()


def main(table: str, timestamp: str, apply: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{table}"
    payload, ingested_at_iso = fetch_snapshot(client, table_id, timestamp)

    response = payload["response"]
    print(f"Source snapshot ({timestamp} UTC):")
    print(f"  original ingested_at: {ingested_at_iso}")
    print(f"  $.response.length:    {len(response)}")
    if isinstance(response, list) and response and isinstance(response[0], dict):
        first_keys = sorted(response[0].keys())
        print(f"  first entry keys:     {first_keys}")
    print(f"Target table: {table_id}")
    print()

    if not apply:
        print("DRY RUN — re-run with --apply to write this snapshot back to the live table.")
        return

    print("Writing snapshot back via WRITE_TRUNCATE...")
    write_back(client, table_id, payload, ingested_at_iso)
    print(f"Done. Run 'inspect_raw_payload.py --table {table}' to confirm.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--table", required=True, help="Raw table name to restore, e.g. RAW_APIF_BL1_LEAGUES")
    parser.add_argument("--timestamp", required=True, help="UTC timestamp to restore from, e.g. '2026-05-07 17:55:00'")
    parser.add_argument("--apply", action="store_true", help="Actually write back. Without this flag, prints the plan only.")
    args = parser.parse_args()
    main(args.table, args.timestamp, args.apply)
