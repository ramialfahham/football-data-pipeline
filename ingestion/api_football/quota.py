"""API error flattening, pipeline error sink, and HTTP quota / pacing helpers."""

from __future__ import annotations

import json
import os
import time

# Updated after each successful `fetch_json` when the provider sends quota headers.
_last_requests_remaining: int | None = None

# When API-Sports returns the daily cap in the JSON body, stop issuing further HTTP in this run
# (avoids hammering /transfers per team and per-fixture bundles after quota is gone).
_http_quota_exhausted: bool = False
_pipeline_errors_for_quota: list[str] | None = None


def reset_http_quota_exhausted() -> None:
    global _http_quota_exhausted
    _http_quota_exhausted = False


def _bind_quota_error_sink(errors: list[str] | None) -> None:
    global _pipeline_errors_for_quota
    _pipeline_errors_for_quota = errors


def _payload_shows_daily_limit_exceeded(data: dict) -> bool:
    for msg in _flatten_api_errors(data.get("errors")):
        low = str(msg).lower()
        if "request limit" in low and "day" in low:
            return True
    return False


def _flag_daily_quota_exhausted_once() -> None:
    global _http_quota_exhausted
    if _http_quota_exhausted:
        return
    _http_quota_exhausted = True
    if _pipeline_errors_for_quota is not None:
        _pipeline_errors_for_quota.append(
            "API daily request limit reached in this run; further HTTP calls were skipped."
        )


def _dedupe_errors_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _flatten_api_errors(raw) -> list[str]:
    """Normalize API `errors` field (empty list, strings, dicts, or list of mixed)."""
    if raw is None:
        return []
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, dict):
        if not raw:
            return []
        parts = []
        for k, v in raw.items():
            if isinstance(v, (dict, list)):
                parts.append(f"{k}: {json.dumps(v, ensure_ascii=True)}")
            else:
                parts.append(f"{k}: {v}")
        return ["; ".join(parts)] if parts else []
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                out.append(json.dumps(item, ensure_ascii=True))
            elif item is not None:
                out.append(str(item))
        return out
    return [str(raw)]


def append_api_errors(data: dict, context: str, sink: list[str]) -> None:
    """Record API body errors next to a pipeline step (guide: prefer body over HTTP code alone)."""
    for msg in _flatten_api_errors(data.get("errors")):
        sink.append(f"{context}: {msg}")


def _request_pause_seconds() -> float:
    """
    Pause after each successful HTTP response.

    When ``API_FOOTBALL_REQUEST_PAUSE_MS`` is unset, default **6600 ms** (~9 calls/min)
    to stay under common free-tier **10 requests/minute** limits. Set to ``0`` for no pause (paid / CI).
    """
    raw = os.getenv("API_FOOTBALL_REQUEST_PAUSE_MS")
    if raw is None or str(raw).strip() == "":
        return 6.6
    try:
        return max(0.0, float(str(raw).strip()) / 1000.0)
    except ValueError:
        return 6.6


def _throttle() -> None:
    delay = _request_pause_seconds()
    if delay:
        time.sleep(delay)


def _maybe_log_quota(response_headers: dict) -> None:
    if os.getenv("API_FOOTBALL_LOG_QUOTA", "").strip() not in ("1", "true", "yes"):
        return
    daily = response_headers.get("x-ratelimit-requests-remaining")
    minute = response_headers.get("X-Ratelimit-Remaining") or response_headers.get(
        "x-ratelimit-remaining"
    )
    if daily is not None or minute is not None:
        print(
            f"[api-football] quota headers: daily_remaining={daily!r} per_minute={minute!r}",
            flush=True,
        )
