"""HTTP GET, pagination merge, and rate-limit handling for API-Football."""

from __future__ import annotations

import os
import time

import requests

from . import quota as errors_quota
from .settings import base_url
from .quota import (
    _flag_daily_quota_exhausted_once,
    _flatten_api_errors,
    _maybe_log_quota,
    _payload_shows_daily_limit_exceeded,
    _payload_shows_minute_rate_limit,
    _throttle,
    record_minute_rate_limit,
)


def fetch_json(path: str, headers: dict, params: dict | None = None) -> dict:
    """
    GET JSON from API-Football. Retries 429 / 5xx once with backoff (guide: safe single retry).

    Also retries once on the PER-MINUTE rate limit, which the provider delivers as HTTP 200 with
    the error in the body rather than as a 429 (#898). Before this, `raise_for_status()` saw a
    healthy response and the call was dropped with ZERO retries, which is how 10 of 18 nightly runs
    lost calls while reporting success.

    BEST EFFORT, deliberately. A per-minute window can take up to 60s to clear and this waits
    `Retry-After` or 3s, so it will not rescue every call. Waiting out a full minute per drop would
    trade run time for a case #897's pacing should already have made rare. The guarantees live
    elsewhere: #897 makes limits rare, #896 makes a drop non-destructive, and the counter below
    makes what remains visible.
    """
    if errors_quota._http_quota_exhausted:
        return {"errors": [], "response": [], "results": 0, "paging": {}}
    url = f"{base_url()}{path}"
    params = dict(params or {})
    for attempt in range(2):
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 429 and attempt == 0:
            ra = response.headers.get("Retry-After", "")
            wait = float(ra) if ra.isdigit() else 3.0
            time.sleep(wait)
            continue
        if 500 <= response.status_code < 600 and attempt == 0:
            time.sleep(1.5)
            continue
        response.raise_for_status()
        data = response.json()
        for key in (
            "x-ratelimit-requests-remaining",
            "X-RateLimit-Requests-Remaining",
            "X-Ratelimit-Requests-Remaining",
        ):
            v = response.headers.get(key)
            if v is not None and str(v).strip().isdigit():
                errors_quota._last_requests_remaining = int(str(v).strip())
                break
        _maybe_log_quota(response.headers)
        _throttle()
        if _payload_shows_daily_limit_exceeded(data):
            _flag_daily_quota_exhausted_once()
            return data
        # The per-minute limit is a 200 carrying a 429's meaning, so give it a 429's single retry.
        # Checked AFTER the daily test: once the daily cap is gone a retry cannot help.
        if _payload_shows_minute_rate_limit(data):
            if attempt == 0:
                ra = response.headers.get("Retry-After", "")
                time.sleep(float(ra) if ra.isdigit() else 3.0)
                continue
            # Retry exhausted and still rejected, so this call is genuinely dropped. Counted here,
            # at the one place an HTTP call happens, so the tally cannot be inflated by a caller
            # that reports the same error twice.
            record_minute_rate_limit(path)
        return data
    raise AssertionError("fetch_json: unreachable")


def result_is_complete(data: dict) -> bool:
    """Whether a just-returned fetch result is safe to supersede stored data with (#896).

    True only when the provider reported no body-level error AND the run's daily-quota flag is not
    set. BOTH signals are required, because the two failure shapes look different:
    a per-minute rate limit arrives as HTTP 200 with the error in the body (so ``response`` is empty
    or partial while the call looks successful), whereas once the daily quota is gone
    ``fetch_json`` short-circuits and returns an empty body with NO error at all. Either signal
    alone misses one of them.

    Call this IMMEDIATELY after the fetch, before issuing another one: the quota flag is
    process-global and latches for the rest of the run.

    Deliberately a function rather than a key on the returned dict. ``_merge_merged_paged`` and the
    manual envelope comprehension in loads/teams.py copies every key it does
    not explicitly exclude straight into the stored raw payload, so an extra key would be persisted
    into three raw tables. It would also be WRONG there: ``_merge_merged_paged`` copies from the
    FIRST source only, so the value would freeze at the first season of a multi-season loop and a
    run whose fourth season was rate-limited would still record the snapshot as complete.

    An empty response with no error counts as COMPLETE: that is the provider reporting no rows, and
    it is indistinguishable from one — a deliberate rule. Stopping at the deliberate page cap
    also counts as complete, because that cap has always bounded the stored snapshot.
    """
    return not (data.get("errors") or []) and not errors_quota._http_quota_exhausted


def _paging_done(data: dict, page: int) -> bool:
    paging = data.get("paging") or {}
    current = int(paging.get("current") or page)
    total = int(paging.get("total") or 1)
    return current >= total


def fetch_merged_paged(
    path: str,
    headers: dict,
    base_params: dict,
    *,
    paginate: bool = True,
    max_pages: int | None = None,
) -> dict:
    """
    Fetch API list endpoints. When ``paginate`` is True, merges all ``page=`` results (e.g. ``/players``).
    When False, sends ``base_params`` only — many endpoints (and free-tier plans) reject ``page``.

    The returned dict's KEY SET IS PART OF THE CONTRACT — do not add to it. Three loaders build the
    raw payload they persist by copying every key except a fixed exclusion list, so a new key lands
    in RAW_APIF_STANDINGS, RAW_APIF_TEAMS and RAW_APIF_FIXTURES_NEXT. To ask
    whether a result may supersede stored data, call :func:`result_is_complete` (#896).
    """
    if not paginate:
        data = fetch_json(path, headers, params=dict(base_params))
        meta = {k: v for k, v in data.items() if k not in ("response", "errors", "results", "paging")}
        out = dict(meta)
        out["errors"] = _flatten_api_errors(data.get("errors"))
        merged = list(data.get("response") or [])
        out["response"] = merged
        out["results"] = len(merged)
        out["paging"] = {"current": 1, "total": 1}
        return out

    limit = max_pages if max_pages is not None else int(os.getenv("API_FOOTBALL_MAX_PAGES", "250"))
    merged: list = []
    meta: dict | None = None
    merged_errors: list[str] = []
    page = 1
    while page <= limit:
        if errors_quota._http_quota_exhausted:
            break
        params = dict(base_params)
        params["page"] = page
        data = fetch_json(path, headers, params=params)
        if meta is None:
            meta = {k: v for k, v in data.items() if k not in ("response", "errors", "results", "paging")}
        merged_errors.extend(_flatten_api_errors(data.get("errors")))
        merged.extend(data.get("response") or [])
        if _paging_done(data, page):
            break
        # Stop at hard page cap (e.g. free tier max page=3) without treating as an error.
        if page >= limit:
            break
        page += 1
    out = dict(meta)
    out["errors"] = merged_errors
    out["response"] = merged
    out["results"] = len(merged)
    out["paging"] = {"current": 1, "total": 1}
    return out
