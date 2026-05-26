"""Fixture coverage tracking — RAW_APIF_FIXTURE_COVERAGE.

WHY THIS TABLE EXISTS
---------------------
The fanout pipeline fetches five endpoints per finished fixture (lineups, events,
stats, fixture players, predictions). Each run only fetches the fixtures that are
still missing at least one endpoint — it never re-fetches what is already covered.

Previously, the pipeline determined coverage by reading the merged JSON blob from
each fanout raw table and scanning it for fixture IDs. With the move to append-only
raw storage (issue #220), blobs no longer exist — each run writes a new row
containing only that run's fetches.

RAW_APIF_FIXTURE_COVERAGE is the replacement: a simple tracking table with one row
per (league_code, fixture_id, endpoint) combination, written once the first time
each combination is successfully fetched. The completeness check and the fanout
gap-detection logic both read from this table instead of parsing raw blobs.

TABLE SCHEMA
------------
    league_code     STRING      — internal competition code (e.g. BL1, WC)
    fixture_id      INT64       — API-Football fixture id
    endpoint        STRING      — one of: LINEUPS, FIXTURE_EVENTS, FIXTURE_STATISTICS,
                                  FIXTURE_PLAYERS, PREDICTIONS
    first_fetched_at TIMESTAMP  — UTC timestamp of the run that first fetched this row

The table is partitioned by DATE(first_fetched_at) so historical coverage records
do not slow down queries that only care about recent fetches. The combination
(league_code, fixture_id, endpoint) is logically unique — once written, a row
is never updated or deleted.

USAGE
-----
    # Read what is already covered (called before fanout to build the gap list):
    covered = read_coverage(client)
    # covered["BL1"]["LINEUPS"] == {12345, 12346, ...}

    # Write coverage for newly fetched fixture-endpoint combinations:
    write_coverage(client, new_rows)
    # new_rows = [{"league_code": "BL1", "fixture_id": 12347, "endpoint": "LINEUPS"}, ...]
"""

from __future__ import annotations

import json
import io
from datetime import date, datetime, timezone
from collections import defaultdict

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .settings import GCP_PROJECT_ID, DATASET_ID

# Finished fixtures whose FIXTURE_STATISTICS response was empty are retried for
# this many days after their kickoff date. After the grace period, an empty
# response is treated as permanent (stats are not coming from the API).
STATS_GRACE_DAYS = 7

# The BigQuery table name for fixture coverage tracking.
COVERAGE_TABLE = "RAW_APIF_FIXTURE_COVERAGE"

# All five fanout endpoints, in the same order used throughout the pipeline.
# The string values here are the canonical endpoint names stored in the table.
FANOUT_ENDPOINTS = (
    "LINEUPS",
    "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS",
    "PREDICTIONS",
)

# Maps from the shell key used in fanout.py to the endpoint name in this table.
# Shell keys are short internal identifiers; endpoint names are the canonical strings.
SHELL_KEY_TO_ENDPOINT: dict[str, str] = {
    "lineups":    "LINEUPS",
    "events":     "FIXTURE_EVENTS",
    "fx_stats":   "FIXTURE_STATISTICS",
    "fx_players": "FIXTURE_PLAYERS",
    "preds":      "PREDICTIONS",
}

# Reverse mapping: endpoint name → shell key.
ENDPOINT_TO_SHELL_KEY: dict[str, str] = {v: k for k, v in SHELL_KEY_TO_ENDPOINT.items()}


def _coverage_table_id() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{COVERAGE_TABLE}"


def ensure_coverage_table(client: bigquery.Client) -> None:
    """Create RAW_APIF_FIXTURE_COVERAGE with date partitioning if it does not exist.

    Safe to call on every pipeline run — create_table with exists_ok=True is a
    no-op if the table already exists.

    Also migrates existing tables that predate the has_data column: if the column
    is absent, it is added as NULLABLE. Existing rows (all written for non-empty
    responses) are left as NULL, which read_coverage treats as True via
    COALESCE(has_data, TRUE) in the aggregation query.
    """
    table_id = _coverage_table_id()
    schema = [
        bigquery.SchemaField("league_code",      "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("fixture_id",        "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("endpoint",          "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("first_fetched_at",  "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("has_data",          "BOOL",      mode="NULLABLE"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="first_fetched_at",
    )
    client.create_table(table, exists_ok=True)

    # Add has_data to tables that were created before this column was introduced.
    existing = client.get_table(table_id)
    if not any(f.name == "has_data" for f in existing.schema):
        new_schema = list(existing.schema) + [
            bigquery.SchemaField("has_data", "BOOL", mode="NULLABLE")
        ]
        existing.schema = new_schema
        client.update_table(existing, ["schema"])


def read_coverage(
    client: bigquery.Client,
) -> dict[str, dict[str, dict[int, bool]]]:
    """Return all fetched fixture IDs grouped by league and endpoint, with their has_data flag.

    Returns a nested dict:
        covered[league_code][endpoint][fixture_id] = has_data

    where has_data is True if the fetch returned non-empty data, False if it was
    empty (and the fixture may be retried within the STATS_GRACE_DAYS window).

    Rows are aggregated by (league_code, fixture_id, endpoint) so that a fixture
    which was retried after an empty response has at most one entry per key. If any
    row for a given key has has_data=True (or NULL, which means a legacy row written
    before this column was added), the aggregate is True — data was received and no
    further retry is needed.

    Returns an empty dict if the coverage table does not exist yet (first ever run).
    """
    table_id = _coverage_table_id()

    # Check table exists before querying to avoid an error on the very first run.
    try:
        client.get_table(table_id)
    except NotFound:
        return {}

    # Aggregate rows so retried fixtures appear once. COALESCE(has_data, TRUE) treats
    # legacy NULL rows (written before the has_data column existed) as True — those rows
    # were only ever written for non-empty responses, so True is the correct semantic.
    # LOGICAL_OR means: if any row for this key has has_data=True, the aggregate is True.
    q = f"""
        SELECT
            league_code,
            fixture_id,
            endpoint,
            LOGICAL_OR(COALESCE(has_data, TRUE)) AS has_data
        FROM `{table_id}`
        GROUP BY league_code, fixture_id, endpoint
    """
    rows = list(client.query(q).result())

    # Build the nested dict: covered[league_code][endpoint][fixture_id] = has_data
    covered: dict[str, dict[str, dict[int, bool]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        covered[row.league_code][row.endpoint][int(row.fixture_id)] = bool(row.has_data)

    # Convert defaultdicts to plain dicts for cleaner downstream usage.
    return {lc: dict(endpoints) for lc, endpoints in covered.items()}


def covered_for_league(
    all_covered: dict[str, dict[str, dict[int, bool]]],
    league_code: str,
    *,
    kickoff_by_id: dict[int, date] | None = None,
) -> dict[str, set[int]]:
    """Return the fixture IDs that should be skipped this run, keyed by shell key.

    Translates endpoint names (LINEUPS, FIXTURE_EVENTS, ...) to the shell keys
    (lineups, events, ...) used throughout fanout.py, so the rest of the fanout
    code does not need to know about the coverage table's naming convention.

    Returns a dict with all five shell keys, each mapping to the set of fixture
    IDs that should NOT be re-fetched. A fixture is excluded from the skip set
    (i.e. will be re-fetched) only when all of the following hold:
      - The endpoint is FIXTURE_STATISTICS
      - has_data is False (previous fetch returned an empty statistics payload)
      - The fixture's kickoff date is known and within STATS_GRACE_DAYS of today

    For all other cases — has_data=True, non-statistics endpoints, or missing
    kickoff date — the fixture is conservatively added to the skip set.

    kickoff_by_id maps fixture_id → kickoff date (UTC calendar day). When omitted,
    the grace-period logic is skipped and all coverage entries are treated as final.
    """
    league_coverage = all_covered.get(league_code, {})
    today = datetime.now(timezone.utc).date()
    result: dict[str, set[int]] = {}

    for shell_key, endpoint in SHELL_KEY_TO_ENDPOINT.items():
        endpoint_data: dict[int, bool] = league_coverage.get(endpoint, {})
        skip_set: set[int] = set()

        for fid, has_data in endpoint_data.items():
            if has_data:
                # Data received — never re-fetch.
                skip_set.add(fid)
            elif endpoint == "FIXTURE_STATISTICS" and kickoff_by_id is not None:
                kickoff = kickoff_by_id.get(fid)
                if kickoff is not None and (today - kickoff).days < STATS_GRACE_DAYS:
                    # Empty response but still within the delivery-delay grace period.
                    # Omit from skip_set so the fixture is retried this run.
                    pass
                else:
                    # Grace period elapsed (or kickoff unknown) — stop retrying.
                    skip_set.add(fid)
            else:
                # Non-statistics endpoint, or no kickoff info — skip conservatively.
                skip_set.add(fid)

        result[shell_key] = skip_set

    return result


def write_coverage(
    client: bigquery.Client,
    new_rows: list[dict],
) -> None:
    """Append newly fetched (league_code, fixture_id, endpoint) combinations.

    Each dict in new_rows must have:
        league_code  str   — e.g. "BL1"
        fixture_id   int   — API fixture id
        endpoint     str   — one of FANOUT_ENDPOINTS

    Rows are written with WRITE_APPEND. The first_fetched_at timestamp is set
    to the current UTC time for all rows in this batch. Duplicate rows (same
    league_code + fixture_id + endpoint from a previous run) will not be written
    because the caller only passes rows that were not already in the coverage
    table — see the gap detection in fanout.py.
    """
    if not new_rows:
        return

    table_id = _coverage_table_id()
    fetched_at = datetime.now(timezone.utc).isoformat()

    # Build NDJSON: one line per row.
    # has_data defaults to True when not supplied — callers that do not set it
    # are writing coverage for endpoints where any response counts as success.
    lines = []
    for row in new_rows:
        lines.append(json.dumps({
            "league_code":     row["league_code"],
            "fixture_id":      int(row["fixture_id"]),
            "endpoint":        row["endpoint"],
            "first_fetched_at": fetched_at,
            "has_data":        bool(row.get("has_data", True)),
        }, ensure_ascii=True))
    ndjson = "\n".join(lines) + "\n"

    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("league_code",      "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("fixture_id",        "INT64",     mode="REQUIRED"),
            bigquery.SchemaField("endpoint",          "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("first_fetched_at",  "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("has_data",          "BOOL",      mode="NULLABLE"),
        ],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND",
    )
    job = client.load_table_from_file(
        io.BytesIO(ndjson.encode("utf-8")), table_id, job_config=job_config
    )
    job.result()
