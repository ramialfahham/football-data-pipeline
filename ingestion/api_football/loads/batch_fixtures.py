"""Fetch finished-fixture details, 20 per /fixtures?ids= call, into RAW_APIF_FIXTURE_DETAILS.

Raw is append-only, so a retried fixture holds one row per attempt and base resolves the versions.
"""

from __future__ import annotations

import io
import json
import time
from datetime import date, datetime, timedelta, timezone

from google.cloud import bigquery

from .. import quota as errors_quota
from ..bigquery import ensure_unified_raw_table
from ..http_client import fetch_json, result_is_complete
from ..quota import append_api_errors
from ..settings import GCP_PROJECT_ID, DATASET_ID, _env_int, raw_table
from .context import CompetitionRunResult, PipelineContext

# The provider accepts at most 20 fixture IDs per /fixtures?ids= call.
_BATCH_SIZE = 20

# Days after kickoff during which empty statistics are retried; the provider delays up to 48 hours.
_STATS_RETRY_DAYS = 3


def _needs_fetch(
    fixture_id: int,
    covered: dict[str, dict[int, bool]],
    kickoff_by_id: dict[int, date],
    retry_cutoff: date,
) -> bool:
    """Whether a finished fixture needs a (re-)fetch; `covered` is this league's coverage entry.

    Decision table:
      Never fetched                            → fetch
      Player stats' second fetch due           → fetch (once; coverage.second_fetch_due)
      Player stats' newer-format refetch due   → fetch (once; coverage.newer_format_refetch_due)
      Fetched, statistics non-empty            → skip (done permanently)
      Fetched, statistics empty, within window → retry (delivery delay expected)
      Fetched, statistics empty, past window   → skip (accept empty permanently)
      Fetched, statistics empty, no kickoff    → skip (can't determine window)
    """
    has_statistics = covered.get("FIXTURE_STATISTICS", {})
    if fixture_id not in has_statistics:
        return True
    if not covered.get("FIXTURE_PLAYERS", {}).get(fixture_id, True):
        return True
    if has_statistics[fixture_id]:
        return False  # statistics present — done
    kickoff = kickoff_by_id.get(fixture_id)
    if kickoff is None:
        return False
    return kickoff >= retry_cutoff


def _finished_fixture_ids(fixtures_response: list[dict]) -> set[int]:
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


def _insert_fixture_rows(
    client: bigquery.Client,
    table_name: str,
    fixture_jsons: list[dict],
    ingested_at: datetime,
    league_code: str,
) -> None:
    """Append one row per fixture to RAW_APIF_FIXTURE_DETAILS; fixture_id comes from the payload."""
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
    """Fetch one batch and append a row per fixture; an incompletely answered batch is discarded."""
    ids_param = "-".join(str(fid) for fid in fixture_ids)
    data = fetch_json("/fixtures", headers=ctx.headers, params={"ids": ids_param})
    append_api_errors(data, f"fixture_details {league_code}", ctx.errors)

    # Checked right after the fetch because the quota flag is process-global and latches.
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
    all_covered: dict[str, dict[str, dict[int, bool]]],
) -> None:
    """Plan every competition's fetches from `all_covered` before making any HTTP call."""
    from ..fixture_scheduling import _fixture_kickoff_by_id

    today = date.today()
    retry_cutoff = today - timedelta(days=_STATS_RETRY_DAYS)
    sleep_s = _env_int("API_FOOTBALL_BATCH_SLEEP_MS", 250) / 1000.0

    plan: list[tuple[str, list[int], set[int]]] = []  # (league_code, to_fetch, retry_ids)
    for result in results:
        response = result.fixtures_merged.get("response", [])
        finished = _finished_fixture_ids(response)
        kickoff_by_id = _fixture_kickoff_by_id(response)
        covered = all_covered.get(result.league_code, {})

        to_fetch = sorted(
            fid for fid in finished
            if _needs_fetch(fid, covered, kickoff_by_id, retry_cutoff)
        )
        retry_ids = {
            fid for fid in to_fetch
            if fid in covered.get("FIXTURE_STATISTICS", {})
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
