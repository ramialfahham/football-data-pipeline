"""Inspect a single RAW_APIF_*_* table's current payload.

Prints schema, row count, latest ingested_at, and a structural summary of the
payload JSON: $.results, $.response (type + length), $.errors. Use to confirm
the table is healthy or to capture evidence when something downstream fails.

Assumes the standard ``as_json_payload=True`` schema: payload (JSON) +
ingested_at (TIMESTAMP).

Usage:
    python scripts/diagnostics/inspect_raw_payload.py --table RAW_APIF_BL1_LEAGUES
"""

from __future__ import annotations

import argparse
import json

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"


def main(table: str) -> None:
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{table}"

    try:
        meta = client.get_table(table_id)
    except NotFound:
        print(f"NOT FOUND: {table_id}")
        return

    print(f"Table:    {table_id}")
    print(f"Created:  {meta.created}")
    print(f"Modified: {meta.modified}")
    print(f"Num rows: {meta.num_rows}")
    print(f"Schema:   {[(f.name, f.field_type) for f in meta.schema]}")
    print()

    if meta.num_rows == 0:
        print("(table is empty)")
        return

    rows = list(client.query(
        f"select ingested_at, to_json_string(payload) as payload_json "
        f"from `{table_id}` order by ingested_at desc limit 1"
    ).result())
    if not rows:
        print("Query returned zero rows.")
        return

    row = rows[0]
    payload = json.loads(row.payload_json)
    response = payload.get("response")
    errors = payload.get("errors")
    results = payload.get("results")
    parameters = payload.get("parameters")

    print(f"Latest ingested_at: {row.ingested_at}")
    print(f"$.results:    {results!r}")
    print(f"$.parameters: {parameters!r}")
    resp_len = len(response) if hasattr(response, "__len__") else "N/A"
    print(f"$.response:   {type(response).__name__}, len={resp_len}")
    print(f"$.errors:     {type(errors).__name__}, value={errors!r}")

    if isinstance(response, list) and response:
        first = response[0]
        if isinstance(first, dict):
            keys = sorted(first.keys())
            print(f"First entry keys: {keys}")
        else:
            print(f"First entry: {first!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--table", required=True, help="Raw table name, e.g. RAW_APIF_BL1_LEAGUES")
    args = parser.parse_args()
    main(args.table)
