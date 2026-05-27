"""Batch fixture ingestion: full sub-data via GET /fixtures?ids=ID1-...-ID20.

Step 2 of the documented two-step ingestion pattern (Step 1 is loads/fixtures.py).
One API call per 20 finished fixtures returns events, lineups, statistics, and players
embedded in the response — replacing the old 5-endpoint-per-fixture fanout.

Storage model: one row per fixture in RAW_APIF_FIXTURE_DETAILS (unified, all leagues).
  league_code STRING    — competition discriminator
  fixture_id  INT64     — for merge-key lookups (partitioned by DATE(ingested_at))
  payload     JSON      — the single fixture object from $.response[n]
  ingested_at TIMESTAMP — when this row was written (UTC)

On the first fetch of a fixture the row is inserted. On retry (empty stats
within STATS_RETRY_DAYS of kickoff) the old row is deleted first so only one
row per (league_code, fixture_id) ever exists. Staging models read payload
directly — no $.response unnesting needed.

Coverage is derived by querying RAW_APIF_FIXTURE_DETAILS directly, filtered by
league_code: any fixture_id already present with non-empty statistics is done.

Rate limiting: the Pro plan allows 300 calls/min burst. Sleeping
API_FOOTBALL_BATCH_SLEEP_MS (default 250 ms) between calls gives ~4 calls/sec.

See docs/api_football_ingestion_blueprint.md for the full API specification.
"""

from __future__ import annotations

import io
import json
import time
from datetime import date, datetime, timedelta, timezone

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .. import quota as errors_quota
from ..bigquery import ensure_unified_raw_table
from ..http_client import fetch_json
from ..quota import append_api_errors
from ..settings import GCP_PROJECT_ID, DATASET_ID, _env_int, raw_table
from .context import CompetitionRunResult, PipelineContext

# API-Football documented limit: up to 20 fixture IDs per /fixtures?ids=... call.
_BATCH_SIZE = 20

# Retry fixtures with empty statistics for this many days after kickoff.
# The API documents up to 48 hours delay; 3 days gives one extra day of buffer.
_STATS_RETRY_DAYS = 3


def _fixture_details_table_id() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('FIXTURE_DETAILS')}"


def _read_fetched_coverage(
    client: bigquery.Client,
    league_code: str,
) -> dict[int, bool]:
    """Return {fixture_id: has_statistics} for all fixtures in RAW_APIF_FIXTURE_DETAILS for this league.

    Each row in FIXTURE_DETAILS stores exactly one fixture's payload.
    has_statistics is True when the fixture's statistics array is non-empty.
    Returns an empty dict when the table does not exist (first run).
    """
    table_id = _fixture_details_table_id()
    try:
        client.get_table(table_id)
    except NotFound:
        return {}

    q = f"""
        SELECT
          CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64) AS fixture_id,
          ARRAY_LENGTH(JSON_QUERY_ARRAY(payload, '$.statistics')) > 0 AS has_statistics
        FROM `{table_id}`
        WHERE JSON_VALUE(payload, '$.fixture.id') IS NOT NULL
          AND league_code = '{league_code}'
    """
    try:
        rows = list(client.query(q).result())
    except Exception:
        return {}

    return {
        int(row.fixture_id): bool(row.has_statistics)
        for row in rows
        if row.fixture_id is not None
    }


def _needs_fetch(
    fixture_id: int,
    fetched: dict[int, bool],
    kickoff_by_id: dict[int, date],
    retry_cutoff: date,
) -> bool:
    """Return True if this finished fixture needs a (re-)fetch.

    Decision table:
      Never fetched                            → fetch
      Fetched, statistics non-empty            → skip (done permanently)
      Fetched, statistics empty, within window → retry (delivery delay expected)
      Fetched, statistics empty, past window   → skip (accept empty permanently)
      Fetched, statistics empty, no kickoff    → skip (can't determine window)
    """
    if fixture_id not in fetched:
        return True
    if fetched[fixture_id]:
        return False  # statistics present — done
    # Empty statistics — retry only within the 3-day window from kickoff.
    kickoff = kickoff_by_id.get(fixture_id)
    if kickoff is None:
        return False
    return kickoff >= retry_cutoff


def _finished_fixture_ids(fixtures_response: list[dict]) -> set[int]:
    """Return fixture IDs whose status is FT, AET, or PEN (match has ended)."""
    out: set[int] = set()
    for row in fixtures_response or []:
        fx = row.get("fixture") or {}
        short = ((fx.get("status") or {}).get("short") or "").strip().upper()
        if short not in {"FT", "AET", "PEN"}:
            continue
        fid = fx.get("id")
        if fid is None:
            continue
        try:
            out.add(int(fid))
        except (TypeError, ValueError):
            continue
    return out


def _delete_fixtures(
    client: bigquery.Client,
    table_id: str,
    fixture_ids: list[int],
    league_code: str,
) -> None:
    """Delete existing rows for the given fixture IDs before re-inserting.

    Used when retrying fixtures that previously had empty statistics, so that
    the table always holds exactly one row per (league_code, fixture_id).
    """
    ids_sql = ", ".join(str(fid) for fid in fixture_ids)
    q = f"""
        DELETE FROM `{table_id}`
        WHERE CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64) IN ({ids_sql})
          AND league_code = '{league_code}'
    """
    client.query(q).result()


def _insert_fixture_rows(
    client: bigquery.Client,
    table_name: str,
    fixture_jsons: list[dict],
    ingested_at: datetime,
    league_code: str,
) -> None:
    """Append one row per fixture to RAW_APIF_FIXTURE_DETAILS.

    Each row: league_code = competition key, payload = fixture object, ingested_at = now.
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    ts = ingested_at.isoformat()
    ndjson = "\n".join(
        json.dumps({"league_code": league_code, "payload": fx, "ingested_at": ts}, ensure_ascii=True)
        for fx in fixture_jsons
    ) + "\n"
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("league_code", "STRING"),
            bigquery.SchemaField("payload", "JSON"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP"),
        ],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND",
    )
    job = client.load_table_from_file(
        io.BytesIO(ndjson.encode("utf-8")), table_id, job_config=job_config
    )
    job.result()


def _fetch_and_persist_batch(
    ctx: PipelineContext,
    league_code: str,
    fixture_ids: list[int],
    retry_ids: set[int],
) -> None:
    """Call GET /fixtures?ids=... and persist one row per fixture.

    For retries (empty stats previously stored), delete the old row first so
    FIXTURE_DETAILS always holds exactly one row per fixture_id.
    """
    ids_param = "-".join(str(fid) for fid in fixture_ids)
    data = fetch_json("/fixtures", headers=ctx.headers, params={"ids": ids_param})
    append_api_errors(data, f"fixture_details {league_code}", ctx.errors)

    response = data.get("response") or []
    if not response:
        return

    table_name = raw_table("FIXTURE_DETAILS")
    table_id = _fixture_details_table_id()
    ensure_unified_raw_table(ctx.client, table_name, include_fixture_id=True)

    # Delete stale rows for any retried fixtures before re-inserting.
    retries_in_batch = [
        fid for fid in fixture_ids if fid in retry_ids
    ]
    if retries_in_batch:
        _delete_fixtures(ctx.client, table_id, retries_in_batch, league_code)

    _insert_fixture_rows(
        ctx.client,
        table_name,
        response,
        datetime.now(timezone.utc),
        league_code,
    )
    ctx.add_loaded(len(response))


def run_batch_fixture_fanout_and_persist(
    ctx: PipelineContext,
    results: list[CompetitionRunResult],
) -> None:
    """Fetch full sub-data for all finished fixtures across all competitions.

    Two-step process per competition:
      1. Read RAW_APIF_FIXTURE_DETAILS (filtered by league_code) to determine which
         finished fixtures already have good statistics. Fixtures missing entirely or
         with empty stats within the 3-day retry window are queued for fetching.
      2. Batch-fetch 20 fixture IDs at a time via GET /fixtures?ids=ID1-...-ID20.
         Each fixture in the response is stored as one row in FIXTURE_DETAILS.
         Retried fixtures (previously empty stats) have their old row deleted first.

    All competitions are planned before any HTTP calls are made.
    """
    from ..fixture_scheduling import _fixture_kickoff_by_id

    today = date.today()
    retry_cutoff = today - timedelta(days=_STATS_RETRY_DAYS)
    sleep_s = _env_int("API_FOOTBALL_BATCH_SLEEP_MS", 250) / 1000.0

    # -----------------------------------------------------------------------
    # Planning pass — determine what needs fetching for each competition.
    # No HTTP calls yet.
    # -----------------------------------------------------------------------
    plan: list[tuple[str, list[int], set[int]]] = []  # (league_code, to_fetch, retry_ids)
    for result in results:
        response = result.fixtures_merged.get("response", [])
        finished = _finished_fixture_ids(response)
        kickoff_by_id = _fixture_kickoff_by_id(response)
        fetched = _read_fetched_coverage(ctx.client, result.league_code)

        to_fetch = sorted(
            fid for fid in finished
            if _needs_fetch(fid, fetched, kickoff_by_id, retry_cutoff)
        )
        retry_ids = {
            fid for fid in to_fetch
            if fid in fetched and not fetched[fid]
        }

        n_done = len(finished) - len(to_fetch)
        print(
            f"[api-football] batch_fanout league={result.league_code} "
            f"finished={len(finished)} done={n_done} to_fetch={len(to_fetch)} "
            f"retries={len(retry_ids)}",
            flush=True,
        )
        if to_fetch:
            plan.append((result.league_code, to_fetch, retry_ids))

    total_fixtures = sum(len(ids) for _, ids, _ in plan)
    total_calls = sum(
        (len(ids) + _BATCH_SIZE - 1) // _BATCH_SIZE for _, ids, _ in plan
    )
    print(
        f"[api-football] batch_fanout total_fixtures_to_fetch={total_fixtures} "
        f"total_api_calls={total_calls}",
        flush=True,
    )

    # -----------------------------------------------------------------------
    # Fetch pass — one batch at a time, sleeping between calls.
    # -----------------------------------------------------------------------
    first_call = True
    for league_code, fixture_ids, retry_ids in plan:
        for i in range(0, len(fixture_ids), _BATCH_SIZE):
            if errors_quota._http_quota_exhausted:
                return
            batch = fixture_ids[i : i + _BATCH_SIZE]
            if not first_call and sleep_s > 0:
                time.sleep(sleep_s)
            first_call = False
            try:
                _fetch_and_persist_batch(ctx, league_code, batch, retry_ids)
            except Exception as e:
                ctx.errors.append(f"batch_fixtures {league_code}: {e}")
