"""Store every team crest and league logo in the private crest bucket, shrunk to two WebP sizes.

The provider's image address does not change when a club changes its badge, so a change is found by
content: each night the objects not checked for `RECHECK_DAYS` days are fetched again and their
SHA-256 compared with the one in the state. One payload row per run, the whole state, goes to
RAW_APIF_CREST_OBJECTS; staging reads the newest row. A failure here never fails the ingest.

The image host is not the API: nothing here sends the API key. Whether its requests count against
the daily quota is measured once, before the first fill, with the account endpoint `/status`, which
does not count; the result is kept in the state.
"""

from __future__ import annotations

import hashlib
import io
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

import requests
from PIL import Image

from .. import quota as errors_quota
from ..bigquery import ensure_raw_table_partitioned, load_json_to_bq, read_latest_payload_json
from ..http_client import fetch_json
from ..settings import CREST_BUCKET, DATASET_ID, GCP_PROJECT_ID, raw_table
from .context import PipelineContext

KINDS = ("teams", "leagues")
SIZES = (48, 104)
STATE_TABLE = raw_table("CREST_OBJECTS")
RECHECK_DAYS = 7
THROTTLE_SECONDS = 0.34
FETCH_TIMEOUT_SECONDS = 20
PREFLIGHT_SAMPLE = 10
PREFLIGHT_MIN_ANSWERED = 5
PREFLIGHT_SETTLE_SECONDS = 5
MAX_FAILURES_IN_A_ROW = 20
API_RESERVE = 1000
MAX_FETCHES_PER_RUN = 4000
STOP_STATUSES = (403, 429)
CACHE_CONTROL = "public, max-age=604800"
WEBP_QUALITY = 90

_DISCOVER_SQL = """
select
  json_value(item, '$.{kind_key}.id') as provider_id,
  json_value(item, '$.{kind_key}.logo') as source_url
from (
  select payload
  from `{project}.{dataset}.{table}`
  qualify row_number() over (partition by league_code order by ingested_at desc) = 1
) as src,
unnest(json_query_array(src.payload, '$.response')) as item
where json_value(item, '$.{kind_key}.id') is not null
  and json_value(item, '$.{kind_key}.logo') is not null
group by provider_id, source_url
"""
_KIND_KEY = {"teams": "team", "leagues": "league"}


class Store(Protocol):
    def exists(self) -> bool: ...

    def put(self, object_name: str, data: bytes) -> None: ...


class GcsStore:
    """The private crest bucket. Listing one object tells a missing bucket from an empty one."""

    def __init__(self, bucket_name: str = CREST_BUCKET, client=None):
        from google.cloud import storage

        self._client = client or storage.Client(project=GCP_PROJECT_ID)
        self._bucket = self._client.bucket(bucket_name)

    def exists(self) -> bool:
        from google.api_core.exceptions import NotFound

        try:
            next(iter(self._client.list_blobs(self._bucket, max_results=1)), None)
        except NotFound:
            return False
        return True

    def put(self, object_name: str, data: bytes) -> None:
        blob = self._bucket.blob(object_name)
        blob.cache_control = CACHE_CONTROL
        blob.upload_from_string(data, content_type="image/webp")


@dataclass
class Fetched:
    status: int
    body: bytes


def fetch_image(url: str, session=None) -> Fetched:
    response = (session or requests).get(url, timeout=FETCH_TIMEOUT_SECONDS)
    return Fetched(response.status_code, response.content if response.status_code == 200 else b"")


def shrink(source: bytes, size: int) -> bytes:
    """The image fitted inside `size` x `size` as WebP, aspect kept and transparency kept."""
    with Image.open(io.BytesIO(source)) as image:
        image = image.convert("RGBA")
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        image.save(out, format="WEBP", quality=WEBP_QUALITY, method=6)
        return out.getvalue()


def object_name(kind: str, provider_id: int | str, size: int) -> str:
    return f"{kind}/{provider_id}-{size}.webp"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def discover(client, kinds=KINDS) -> dict[tuple[str, int], str]:
    """Every (kind, provider id) with the image address the provider's latest list gives it."""
    found: dict[tuple[str, int], str] = {}
    for kind in kinds:
        table = raw_table(kind.upper())
        sql = _DISCOVER_SQL.format(
            kind_key=_KIND_KEY[kind], project=GCP_PROJECT_ID, dataset=DATASET_ID, table=table
        )
        for row in client.query(sql).result():
            try:
                found[(kind, int(row["provider_id"]))] = row["source_url"]
            except (TypeError, ValueError):
                continue
    return found


def plan(
    discovered: dict[tuple[str, int], str],
    state: dict[tuple[str, int], dict],
    now: datetime,
    budget: int,
) -> list[tuple[str, int, str]]:
    """What to fetch: every id with no state first, then the longest-unchecked ones past the window."""
    due_before = now - timedelta(days=RECHECK_DAYS)
    new = sorted(key for key in discovered if key not in state)
    stale = sorted(
        (key for key in discovered if key in state and datetime.fromisoformat(state[key]["checked_at"]) <= due_before),
        key=lambda key: state[key]["checked_at"],
    )
    return [(kind, pid, discovered[(kind, pid)]) for kind, pid in (new + stale)[: max(0, budget)]]


def parse_state(payload: dict | None) -> tuple[dict[tuple[str, int], dict], dict]:
    if not payload:
        return {}, {}
    objects = {(o["kind"], int(o["id"])): o for o in payload.get("objects", [])}
    return objects, payload.get("preflight") or {}


def _status_numbers(headers: dict) -> tuple[int, int]:
    """(requests used today, daily limit) from the account endpoint; (0, 0) when it cannot be read."""
    data = fetch_json("/status", headers)
    requests_block = (data.get("response") or {}).get("requests") if isinstance(data.get("response"), dict) else None
    requests_block = requests_block or {}
    return int(requests_block.get("current") or 0), int(requests_block.get("limit_day") or 0)


def _record(state: dict, kind: str, pid: int, url: str, now: datetime, fetched: Fetched, store: Store) -> str:
    """Apply one fetch to the state and the bucket; return what happened."""
    key = (kind, pid)
    # A copy, put in the state only after the files are written: a failed write keeps the old entry,
    # so the image is checked again on the next run.
    entry = dict(state.get(key) or {"kind": kind, "id": pid})
    entry["source_url"] = url
    entry["checked_at"] = _iso(now)
    if fetched.status == 404:
        entry["status"] = "missing"
        entry.pop("sha256", None)
        state[key] = entry
        return "missing"
    digest = hashlib.sha256(fetched.body).hexdigest()
    if entry.get("status") == "ok" and entry.get("sha256") == digest:
        state[key] = entry
        return "unchanged"
    for size in SIZES:
        store.put(object_name(kind, pid, size), shrink(fetched.body, size))
    entry.update({"status": "ok", "sha256": digest, "fetched_at": _iso(now)})
    state[key] = entry
    return "stored"


def run(
    ctx: PipelineContext,
    *,
    store: Store | None = None,
    discovered: dict[tuple[str, int], str] | None = None,
    fetch: Callable[[str], Fetched] = fetch_image,
    status_numbers: Callable[[dict], tuple[int, int]] = _status_numbers,
    now: datetime | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """The crest phase. Returns a summary; raises nothing a caller must handle."""
    # The table exists from the first run on, empty or not: dbt reads it as a source every night.
    ensure_raw_table_partitioned(ctx.client, STATE_TABLE)
    store = store or GcsStore()
    now = now or _now()
    summary = {"stored": 0, "unchanged": 0, "missing": 0, "failed": 0, "stopped": None, "skipped": None}
    if errors_quota._http_quota_exhausted:
        summary["skipped"] = "the daily API quota is used up, so the account counter cannot be read"
        return summary
    if not store.exists():
        summary["skipped"] = "the crest bucket does not exist"
        return summary

    state, preflight = parse_state(read_latest_payload_json(ctx.client, STATE_TABLE))
    found = discovered if discovered is not None else discover(ctx.client)
    queue = plan(found, state, now, MAX_FETCHES_PER_RUN)
    changed = False
    failures_in_a_row = 0

    def step(kind: str, pid: int, url: str) -> bool:
        """One image applied to the state; False stops the phase. One bad image never costs the rest."""
        nonlocal changed, failures_in_a_row
        try:
            result = fetch(url)
            sleep(THROTTLE_SECONDS)
            if result.status in STOP_STATUSES:
                summary["stopped"] = f"{result.status} on {url}"
                return False
            if result.status not in (200, 404):
                raise ValueError(f"HTTP {result.status}")
            outcome = _record(state, kind, pid, url, now, result, store)
        except Exception as error:
            summary["failed"] += 1
            failures_in_a_row += 1
            print(f"[crests] {kind}/{pid} failed: {error}", flush=True)
            if failures_in_a_row >= MAX_FAILURES_IN_A_ROW:
                summary["stopped"] = f"{failures_in_a_row} failures in a row"
                return False
            return True
        failures_in_a_row = 0
        summary[outcome] += 1
        changed = True
        return True

    try:
        if "images_count_quota" not in preflight and queue:
            before, limit = status_numbers(ctx.headers)
            if limit == 0:
                summary["skipped"] = "the account counter is unreadable, so the quota effect of images is not measured"
                queue = []
            else:
                sample, queue = queue[:PREFLIGHT_SAMPLE], queue[PREFLIGHT_SAMPLE:]
                answered = summary["stored"] + summary["unchanged"] + summary["missing"]
                if all(step(kind, pid, url) for kind, pid, url in sample):
                    sleep(PREFLIGHT_SETTLE_SECONDS)
                    after, limit_after = status_numbers(ctx.headers)
                    answered = summary["stored"] + summary["unchanged"] + summary["missing"] - answered
                    if limit_after > 0 and answered >= PREFLIGHT_MIN_ANSWERED:
                        preflight = {
                            "images_count_quota": after > before,
                            "measured_at": _iso(now),
                            "requests_before": before,
                            "requests_after": after,
                        }
                        changed = True
                        print(f"[crests] preflight {preflight}", flush=True)
                if "images_count_quota" not in preflight:
                    summary["skipped"] = "the quota effect of images is not measured yet: no fill tonight"
                    queue = []

        if preflight.get("images_count_quota") and queue:
            used, limit = status_numbers(ctx.headers)
            if limit:
                queue = queue[: max(0, limit - used - API_RESERVE)]
            else:
                summary["skipped"] = "the account counter is unreadable: no fetch tonight"
                queue = []

        for kind, pid, url in queue:
            if not step(kind, pid, url):
                break
    finally:
        if changed:
            objects = sorted(state.values(), key=lambda o: (o["kind"], o["id"]))
            payload = {"version": 1, "preflight": preflight, "objects": objects}
            load_json_to_bq(ctx.client, STATE_TABLE, payload, as_json_payload=True, append=True)
            ctx.add_loaded(1)
    return summary
