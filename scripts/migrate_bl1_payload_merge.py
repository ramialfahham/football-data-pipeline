"""Merge D1 historical payload data into the canonical RAW_APIF_BL1_* tables.

After migrate_bl1_raw_table_rename.py ran:
  - RAW_APIF_BL1_* = formerly RAW_BL1_APIF_* (recent ingestion, less history)
  - RAW_D1_APIF_*  = original tables (more historical seasons, now orphaned)

This script reads both payloads per endpoint, merges them using the same
functions the ingestion pipeline uses (D1 = existing base, BL1 = incoming and
wins on any key conflict since it has fresher API data), then writes the merged
result back to RAW_APIF_BL1_*.

Merge keys per endpoint:
  FIXTURES_NEXT      : fixture.id
  LEAGUES            : no merge — keep BL1 (latest season catalog)
  STANDINGS          : league.season
  ROUNDS             : season block
  TEAMS              : (team.id, league.season)
  INJURIES           : (season, player.id, team.id, fixture.id, type, reason)
  TRANSFERS          : player.id
  LINEUPS            : fixture_id
  FIXTURE_EVENTS     : fixture_id
  FIXTURE_STATISTICS : fixture_id
  FIXTURE_PLAYERS    : fixture_id
  PREDICTIONS        : fixture_id
  PLAYERS            : (team_id, season)
  INGEST_CURSOR      : no merge — keep BL1 (live cursor state)

Usage:
    python scripts/migrate_bl1_payload_merge.py [--dry-run]
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from ingestion.api_football.merge import (
    merge_fanout_batched,
    merge_fixtures_envelope,
    merge_injuries_envelope,
    merge_standings_envelope,
    merge_teams_envelope,
    merge_transfers_envelope,
)

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"
LEAGUE_CODE = "BL1"

FANOUT_ENDPOINTS = [
    "LINEUPS",
    "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS",
    "PREDICTIONS",
]

SKIP_MERGE_ENDPOINTS = [
    "LEAGUES",
    "INGEST_CURSOR",
]


def _read_payload(client: bigquery.Client, table_id: str) -> dict | None:
    try:
        table = client.get_table(table_id)
    except NotFound:
        return None
    colnames = {f.name for f in table.schema}
    if "payload" not in colnames:
        return None
    if "ingested_at" in colnames:
        q = f"SELECT payload FROM `{table_id}` ORDER BY ingested_at DESC LIMIT 1"
    elif "ingested_datetime" in colnames:
        q = f"SELECT payload FROM `{table_id}` ORDER BY ingested_datetime DESC LIMIT 1"
    else:
        q = f"SELECT payload FROM `{table_id}` LIMIT 1"
    job = client.query(q)
    try:
        # Use Storage Read API (gRPC) to handle payloads > REST's 20 MiB row limit.
        arrow_table = job.result().to_arrow(create_bqstorage_client=True)
        if arrow_table.num_rows == 0:
            return None
        pl = arrow_table.column("payload")[0].as_py()
    except Exception:
        # Fallback for tables where Storage API isn't needed / pyarrow type issues.
        pl = None
        for row in job.result():
            pl = row["payload"]
            break
    if pl is None:
        return None
    if isinstance(pl, dict):
        return pl
    if isinstance(pl, (bytes, bytearray)):
        pl = pl.decode("utf-8")
    if isinstance(pl, str):
        return json.loads(pl)
    return dict(pl)


def _write_payload(client: bigquery.Client, table_id: str, payload: dict, dry_run: bool) -> None:
    if dry_run:
        n = len((payload.get("response") or []))
        print(f"    would write {n} response rows to {table_id}")
        return
    row = {"payload": payload, "ingested_at": datetime.now(timezone.utc).isoformat()}
    line = json.dumps(row, ensure_ascii=True) + "\n"
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("payload", "JSON"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP"),
        ],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_TRUNCATE",
    )
    job = client.load_table_from_file(io.BytesIO(line.encode("utf-8")), table_id, job_config=job_config)
    job.result()


def _merge_rounds(d1: dict, bl1: dict | None) -> dict:
    """Merge two multi-season rounds payloads. BL1 wins on season conflict."""
    by_s: dict[int, dict] = {}
    for blk in (d1.get("response") or []):
        if isinstance(blk, dict) and blk.get("season") is not None:
            try:
                by_s[int(blk["season"])] = blk
            except (TypeError, ValueError):
                pass
    for blk in ((bl1 or {}).get("response") or []):
        if isinstance(blk, dict) and blk.get("season") is not None:
            try:
                by_s[int(blk["season"])] = blk
            except (TypeError, ValueError):
                pass
    resp = [by_s[s] for s in sorted(by_s.keys())]
    base = bl1 or d1
    out = {k: v for k, v in base.items() if k not in ("response", "errors", "results", "paging")}
    out["response"] = resp
    out["errors"] = list((base.get("errors") or []))
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out


def _merge_players(d1: dict, bl1: dict | None) -> dict:
    """Merge squad player payloads. BL1 wins on (team_id, season) conflict."""
    by_k: dict[tuple[int, int], dict] = {}
    for row in (d1.get("response") or []):
        try:
            by_k[(int(row["team_id"]), int(row["season"]))] = row
        except (KeyError, TypeError, ValueError):
            pass
    for row in ((bl1 or {}).get("response") or []):
        try:
            by_k[(int(row["team_id"]), int(row["season"]))] = row
        except (KeyError, TypeError, ValueError):
            pass
    resp = [by_k[k] for k in sorted(by_k.keys())]
    base = bl1 or d1
    out = {k: v for k, v in base.items() if k not in ("response", "errors", "results", "paging")}
    out["league_code"] = LEAGUE_CODE
    out["response"] = resp
    out["errors"] = list((base.get("errors") or []))
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out


def main(dry_run: bool) -> None:
    client = bigquery.Client(project=PROJECT)
    errors: list[str] = []

    endpoints = [
        "FIXTURES_NEXT",
        "LEAGUES",
        "STANDINGS",
        "ROUNDS",
        "TEAMS",
        "INJURIES",
        "TRANSFERS",
        "LINEUPS",
        "FIXTURE_EVENTS",
        "FIXTURE_STATISTICS",
        "FIXTURE_PLAYERS",
        "PREDICTIONS",
        "PLAYERS",
        "INGEST_CURSOR",
    ]

    for ep in endpoints:
        d1_table = f"{PROJECT}.{DATASET}.RAW_D1_APIF_{ep}"
        bl1_table = f"{PROJECT}.{DATASET}.RAW_APIF_BL1_{ep}"

        print(f"\n[{ep}]")

        if ep in SKIP_MERGE_ENDPOINTS:
            print(f"  SKIP merge (keep BL1 as authoritative for {ep})")
            continue

        d1_payload = _read_payload(client, d1_table)
        if d1_payload is None:
            print(f"  D1 table missing or empty — nothing to merge")
            continue

        d1_n = len((d1_payload.get("response") or []))

        bl1_payload = _read_payload(client, bl1_table)
        bl1_n = len((bl1_payload or {}).get("response") or [])

        print(f"  D1 response rows={d1_n}  BL1 response rows={bl1_n}")

        try:
            if ep == "FIXTURES_NEXT":
                merged = merge_fixtures_envelope(d1_payload, bl1_payload or {"response": []})
            elif ep == "STANDINGS":
                merged = merge_standings_envelope(d1_payload, bl1_payload or {"response": []})
            elif ep == "ROUNDS":
                merged = _merge_rounds(d1_payload, bl1_payload)
            elif ep == "TEAMS":
                merged = merge_teams_envelope(d1_payload, bl1_payload or {"response": []})
            elif ep == "INJURIES":
                merged = merge_injuries_envelope(d1_payload, bl1_payload or {"response": []})
            elif ep == "TRANSFERS":
                merged = merge_transfers_envelope(d1_payload, bl1_payload or {"response": []})
            elif ep in FANOUT_ENDPOINTS:
                merged = merge_fanout_batched(
                    d1_payload,
                    bl1_payload or {"response": []},
                    league_code=LEAGUE_CODE,
                    valid_fixture_ids=None,
                )
            elif ep == "PLAYERS":
                merged = _merge_players(d1_payload, bl1_payload)
            else:
                print(f"  SKIP (no merge strategy defined for {ep})")
                continue
        except Exception as e:
            errors.append(f"{ep}: merge error: {e}")
            print(f"  FAIL merge: {e}", file=sys.stderr)
            continue

        merged_n = len((merged.get("response") or []))
        gain = merged_n - bl1_n
        print(f"  merged response rows={merged_n} (gained {gain:+d} rows from D1)")

        if merged_n < bl1_n:
            msg = (
                f"{ep}: merged row count {merged_n} < BL1 row count {bl1_n} — "
                "aborting write to prevent data loss"
            )
            errors.append(msg)
            print(f"  ABORT {msg}", file=sys.stderr)
            continue

        try:
            _write_payload(client, bl1_table, merged, dry_run)
            if not dry_run:
                print(f"  OK written to {bl1_table}")
        except Exception as e:
            errors.append(f"{ep}: write error: {e}")
            print(f"  FAIL write: {e}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    if not dry_run:
        print("\nDone. D1 tables still exist as backup — drop manually once verified.")
    else:
        print("\nDry run complete. No data written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
