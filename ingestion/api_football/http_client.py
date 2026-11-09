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
    """GET JSON from API-Football, retrying 429, 5xx and the per-minute rate limit once.

    The per-minute limit arrives as HTTP 200 with the error in the body. The retry is best effort:
    it waits `Retry-After` or 3s, which may not outlast the window.
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
        # Checked after the daily test: once the daily cap is gone a retry cannot help.
        if _payload_shows_minute_rate_limit(data):
            if attempt == 0:
                ra = response.headers.get("Retry-After", "")
                time.sleep(float(ra) if ra.isdigit() else 3.0)
                continue
            # Counted here, the one place an HTTP call happens, so callers cannot double-count.
            record_minute_rate_limit(path)
        return data
    raise AssertionError("fetch_json: unreachable")


def result_is_complete(data: dict) -> bool:
    """Whether a fetch result is safe to supersede stored data with.

    Both signals are needed: a per-minute limit is an in-body error on a 200, while an exhausted
    daily quota makes ``fetch_json`` return an empty body with no error. Call it immediately after
    the fetch, since the quota flag is process-global and latches for the rest of the run.
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
    """Fetch a list endpoint, merging all ``page=`` results when ``paginate`` is True.

    Do not add keys to the returned dict: loaders copy every key except a fixed exclusion list
    into the raw payload. Use :func:`result_is_complete` to ask whether a result is complete.
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
