"""HTTP GET, pagination merge, and rate-limit handling for API-Football."""

from __future__ import annotations

import os
import time

import requests

from . import errors_quota
from .config import base_url
from .errors_quota import (
    _flag_daily_quota_exhausted_once,
    _flatten_api_errors,
    _maybe_log_quota,
    _payload_shows_daily_limit_exceeded,
    _throttle,
)


def fetch_json(path: str, headers: dict, params: dict | None = None) -> dict:
    """
    GET JSON from API-Football. Retries 429 / 5xx once with backoff (guide: safe single retry).
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
    raise AssertionError("fetch_json: unreachable")


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
