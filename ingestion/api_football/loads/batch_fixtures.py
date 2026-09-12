"""Batch fixture ingestion: full sub-data via GET /fixtures?ids=ID1-...-ID20.

Step 2 of the documented two-step ingestion pattern (Step 1 is loads/fixtures.py).
One API call per 20 finished fixtures returns events, lineups, statistics, and players
embedded in the response — replacing the old 5-endpoint-per-fixture fanout.

Storage model: one row per fixture PER FETCH in RAW_APIF_FIXTURE_DETAILS (unified, all leagues).
  league_code STRING    — competition discriminator
  fixture_id  INT64     — for per-fixture lookups (partitioned by DATE(ingested_at))
  payload     JSON      — the single fixture object from $.response[n]
  ingested_at TIMESTAMP — when this row was written (UTC)

APPEND ONLY. On the first fetch of a fixture a row is inserted. On retry (empty stats
within STATS_RETRY_DAYS of kickoff) another row is inserted and NOTHING is removed, so
a retried fixture holds one row per attempt. Staging models read payload directly and
faithfully — no $.response unnesting, no dedup — and base resolves the versions by
entity key with latest-ingest-wins.

⚠ Raw therefore holds every version the provider ever gave us, including versions that
contradict each other. That is deliberate ("raw keeps both versions").
The delete that used to run here destroyed 29 real events across 5 fixtures because a
retry chasing late statistics returned fewer events, and one row bundles lineups, events,
statistics and player stats together.

Coverage is derived by querying RAW_APIF_FIXTURE_DETAILS directly, filtered by
league_code: a fixture is done once ANY stored row for it carries non-empty
statistics. That LOGICAL_OR aggregation is what makes the multi-row state safe to read.

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
from ..http_client import fetch_json, result_is_complete
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

    has_statistics is True when the fixture's statistics array is non-empty.
    Returns an empty dict when the table does not exist (first run).

    AGGREGATED PER FIXTURE, and under append-only raw that is load-bearing rather than defensive:
    the table is append-only, so a retried fixture holds one row per attempt as a matter of
    course. Reading row-by-row into a dict would make the answer depend on which row happened to
    land last, and BigQuery does not promise an order — an older empty-statistics row could mask
    a complete one, and the fixture would be re-fetched every run until its window closed,
    burning quota to no effect. LOGICAL_OR answers the question actually being asked, "do we hold
    statistics for this fixture anywhere", and is order-independent.

    ⚠ This aggregation shipped for a narrower reason and turned out to be the precondition the
    append-only rule needed. Do not "simplify" it back to a per-row read.
    """
    table_id = _fixture_details_table_id()
    try:
        client.get_table(table_id)
    except NotFound:
        return {}

    q = f"""
        SELECT
          CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64) AS fixture_id,
          LOGICAL_OR(
            ARRAY_LENGTH(JSON_QUERY_ARRAY(payload, '$.statistics')) > 0
          ) AS has_statistics
        FROM `{table_id}`
        WHERE JSON_VALUE(payload, '$.fixture.id') IS NOT NULL
          AND league_code = '{league_code}'
        GROUP BY fixture_id
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


# REMOVED: `_delete_fixtures`, the delete-on-retry. This is the one that cost real
# data. A fixture row bundles lineups, events, statistics and player stats TOGETHER, so a retry
# chasing late statistics could come back richer in one section and poorer in another, and the
# delete made the poorer answer the only surviving one. MEASURED on fixture 1564795: 27 events
# stored, 17 returned by the retry, an entire penalty shootout destroyed and unrecoverable
# because the provider no longer returns it.
#
# The rule, verbatim: "raw keeps both versions." It applies to every raw table. Both payloads
# now land and BASE decides: `base_apif__fixture_events` dedups
# `partition by (league_code, fixture_id, event_index) order by raw_ingested_at desc`, which on
# that fixture yields 27 — indices 0-16 from the new payload, 17-26 surviving from the old.
# Do NOT restore this as a regression fix; see `.claude/task/escalations.log`.


def _insert_fixture_rows(
    client: bigquery.Client,
    table_name: str,
    fixture_jsons: list[dict],
    ingested_at: datetime,
    league_code: str,
) -> None:
    """Append one row per fixture to RAW_APIF_FIXTURE_DETAILS.

    Each row:
      league_code = competition key
      fixture_id  = top-level merge key, extracted from payload $.fixture.id
      payload     = full fixture object
      ingested_at = UTC timestamp of this write
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    ts = ingested_at.isoformat()

    def _extract_fixture_id(fx: dict) -> int | None:
        fid = (fx.get("fixture") or {}).get("id")
        if fid is None:
            return None
        try:
            return int(fid)
        except (TypeError, ValueError):
            return None

    ndjson = "\n".join(
        json.dumps(
            {
                "league_code": league_code,
                "fixture_id": _extract_fixture_id(fx),
                "payload": fx,
                "ingested_at": ts,
            },
            ensure_ascii=True,
        )
        for fx in fixture_jsons
    ) + "\n"
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("league_code", "STRING"),
            bigquery.SchemaField("fixture_id", "INT64"),
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
) -> None:
    """Call GET /fixtures?ids=... and append one row per fixture returned.

    Nothing is deleted. A retried fixture gains a second row and base resolves the two by
    entity key ("raw keeps both versions" — see the note above `_insert_fixture_rows`).

    #896 still applies, and still returns before the write: a batch the provider did not answer
    cleanly is discarded whole and retried next run. It is no longer the thing standing between
    a shrunken answer and permanent loss — append-only is — but writing a known-partial payload
    would still put a worse row in front of base for no reason, and the fixture would look
    touched when it was not.
    """
    ids_param = "-".join(str(fid) for fid in fixture_ids)
    data = fetch_json("/fixtures", headers=ctx.headers, params={"ids": ids_param})
    append_api_errors(data, f"fixture_details {league_code}", ctx.errors)

    # #896: an incomplete fetch must never be written. Checked immediately after the fetch —
    # the quota flag is process-global and latches for the rest of the run, so a later check
    # would misreport this batch.
    if not result_is_complete(data):
        ctx.errors.append(
            f"fixture_details {league_code}: INCOMPLETE fetch — batch DISCARDED, prior "
            f"payloads kept (#896); retries next run"
        )
        return

    response = data.get("response") or []
    if not response:
        return

    table_name = raw_table("FIXTURE_DETAILS")
    ensure_unified_raw_table(ctx.client, table_name, include_fixture_id=True)

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
         Each fixture in the response is appended as one row in FIXTURE_DETAILS.
         Retried fixtures (previously empty stats) keep their earlier row as well.

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
                _fetch_and_persist_batch(ctx, league_code, batch)
            except Exception as e:
                ctx.errors.append(f"batch_fixtures {league_code}: {e}")
