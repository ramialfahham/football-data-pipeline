"""Entry point: runs the API-Football → BigQuery raw load locally, in CI or as a Cloud Function."""

from __future__ import annotations

from .orchestrator import _load_api_football

try:
    import functions_framework

    load_api_football = functions_framework.http(_load_api_football)
except ImportError:
    load_api_football = _load_api_football


if __name__ == "__main__":
    class _Request:
        pass

    body, status = load_api_football(_Request())
    print(body, flush=True)
    # Exit codes: 0 ok, 1 pipeline error, 2 lock held, 3 completeness.
    if status == 409:
        raise SystemExit(2)
    if status == 503:
        raise SystemExit(3)
    raise SystemExit(0 if status == 200 else 1)
