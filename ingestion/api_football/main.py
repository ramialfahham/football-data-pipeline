"""
API-Football → BigQuery raw loads (D1 MVP).

**Ingestion model:** one job loads the raw tables this repo defines (fixtures, league
metadata, standings, teams, squad ``/players``, and per-fixture bundles).
There is no hidden “extra” data tier—only API coverage and your plan’s limits.

**Configuration:** unset ``API_FOOTBALL_INGEST_PROFILE`` for the warehouse default
(every season the API lists for D1, no slow pacing, generous page caps via ``setdefault``).
Set ``API_FOOTBALL_INGEST_PROFILE=default`` (or ``economy``) for free-tier pacing and a
single inferred season.

Follows the API-Football response contract: check `errors`, then `paging`, then `response`.

Implementation is split under the same package for easier iteration:

- ``config`` — env, constants, league ids
- ``errors_quota`` — error flattening, quota flags, pacing
- ``http_client`` — GET + merged pagination
- ``seasons`` — season lists, fixture params, envelope merges
- ``fanout`` — fixture ordering, coverage, cursor, squad pulls
- ``bq`` — dataset ensure + loads
- ``pipeline`` — thin job runner
- ``loads/`` — one module per ingest concern (fixtures, teams, fanout, …)

References:

- https://www.api-football.com/documentation-v3
- https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide
"""

from __future__ import annotations

from .orchestrator import _load_api_football

try:
    import functions_framework

    load_api_football = functions_framework.http(_load_api_football)
except ImportError:
    load_api_football = _load_api_football


if __name__ == "__main__":
    # Local / CI: load D1 raw tables into BigQuery without Cloud Run.
    # From repo root: set PYTHONPATH=. and API_FOOTBALL_API_KEY, then:
    #   python -m ingestion.api_football.main
    # Exit: 0 ok, 1 error, 2 lock (409), 3 completeness (503).
    class _Request:
        pass

    body, status = load_api_football(_Request())
    print(body, flush=True)
    # Exit codes for schedulers / CI: 0 ok, 1 pipeline error, 2 lock held, 3 completeness.
    if status == 409:
        raise SystemExit(2)
    if status == 503:
        raise SystemExit(3)
    raise SystemExit(0 if status == 200 else 1)
