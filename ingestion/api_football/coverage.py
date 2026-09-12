"""Fixture fanout coverage — derived from RAW_APIF_FIXTURE_DETAILS.

WHY THIS MODULE EXISTS
----------------------
The fanout pipeline fetches a bundle of sub-data per finished fixture (lineups,
events, statistics, players) via GET /fixtures?ids=... Each run only fetches the
fixtures that are still missing data — it never re-fetches what is already covered.

"Coverage" — which (league_code, fixture_id, endpoint) combinations already have
data — is derived directly from RAW_APIF_FIXTURE_DETAILS, the append-only table
that stores one row per fetch of a fixture (its full payload; a retried fixture
therefore has several, and the query below aggregates them). There is no separate
tracking table: the fanout data IS the source of truth, so coverage can never
drift out of sync with it. (This replaced an earlier RAW_APIF_FIXTURE_COVERAGE
tracking table — see issue #221 — which was a denormalized mirror that the live
pipeline never updated.)

COVERAGE SEMANTICS (per endpoint)
---------------------------------
    LINEUPS / FIXTURE_EVENTS / FIXTURE_PLAYERS
        Covered once the fixture has been fetched at all (its row exists). The
        API does not always return these arrays, and an empty array is not a
        gap we can close by re-fetching, so presence of the fixture row counts.
    FIXTURE_STATISTICS
        Covered only when the statistics array is non-empty. Empty statistics on
        a finished fixture is usually a delivery delay, so it is retried within
        STATS_GRACE_DAYS of kickoff (see covered_for_league).

API-Football predictions are deliberately NOT ingested (we build our own), so
there is no PREDICTIONS endpoint here.

USAGE
-----
    covered = read_coverage(client)
    # covered["BL1"]["FIXTURE_STATISTICS"][12345] == True   (stats present)
    # covered["BL1"]["LINEUPS"][12345]            == True   (fixture fetched)
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from collections import defaultdict

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .settings import GCP_PROJECT_ID, DATASET_ID, raw_table

# Finished fixtures whose FIXTURE_STATISTICS response was empty are retried for
# this many days after their kickoff date. After the grace period, an empty
# response is treated as permanent (stats are not coming from the API).
STATS_GRACE_DAYS = 7

# The four fanout endpoints bundled in each RAW_APIF_FIXTURE_DETAILS payload.
# The value is the payload array whose non-emptiness must be checked, or None
# when the fixture being fetched at all is sufficient to count as covered.
ENDPOINT_REQUIRES_NONEMPTY: dict[str, str | None] = {
    "LINEUPS":            None,
    "FIXTURE_EVENTS":     None,
    "FIXTURE_STATISTICS": "statistics",
    "FIXTURE_PLAYERS":    None,
}

# All fanout endpoints, in the canonical order used throughout the pipeline.
FANOUT_ENDPOINTS = tuple(ENDPOINT_REQUIRES_NONEMPTY.keys())

# Maps the shell key used in fanout scheduling to the endpoint name here.
SHELL_KEY_TO_ENDPOINT: dict[str, str] = {
    "lineups":    "LINEUPS",
    "events":     "FIXTURE_EVENTS",
    "fx_stats":   "FIXTURE_STATISTICS",
    "fx_players": "FIXTURE_PLAYERS",
}

# Reverse mapping: endpoint name → shell key.
ENDPOINT_TO_SHELL_KEY: dict[str, str] = {v: k for k, v in SHELL_KEY_TO_ENDPOINT.items()}


def _fixture_details_table_id() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('FIXTURE_DETAILS')}"


def read_coverage(
    client: bigquery.Client,
) -> dict[str, dict[str, dict[int, bool]]]:
    """Return fanout coverage grouped by league and endpoint, derived from FIXTURE_DETAILS.

    Returns a nested dict (same shape the old coverage-table reader returned, so
    downstream callers are unchanged):
        covered[league_code][endpoint][fixture_id] = has_data

    has_data is True when the endpoint's data is present (see COVERAGE SEMANTICS
    in the module docstring). FIXTURE_STATISTICS is True only for a non-empty
    statistics array; the other three endpoints are True for every fetched fixture.

    Rows are aggregated by (league_code, fixture_id) with LOGICAL_OR because a
    fixture legitimately has more than one row: the table is append-only and a
    retried fixture keeps one row per attempt ("raw keeps both versions"). The
    aggregate answers "do we hold statistics for this fixture
    anywhere", which is order-independent — a per-row read would let an older
    empty-statistics row mask a newer complete one and re-fetch it every run.

    Returns an empty dict if RAW_APIF_FIXTURE_DETAILS does not exist yet (first
    ever run, before any fanout has happened).
    """
    table_id = _fixture_details_table_id()

    # Check the table exists before querying to avoid an error on the very first run.
    try:
        client.get_table(table_id)
    except NotFound:
        return {}

    # One row per fixture: did this fixture's statistics array ever arrive non-empty?
    # The other three endpoints count as covered whenever the fixture row exists.
    q = f"""
        SELECT
            league_code,
            CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64) AS fixture_id,
            LOGICAL_OR(ARRAY_LENGTH(JSON_QUERY_ARRAY(payload, '$.statistics')) > 0)
                AS has_statistics
        FROM `{table_id}`
        WHERE JSON_VALUE(payload, '$.fixture.id') IS NOT NULL
        GROUP BY league_code, fixture_id
    """
    rows = list(client.query(q).result())

    covered: dict[str, dict[str, dict[int, bool]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        lc = row.league_code
        fid = int(row.fixture_id)
        has_stats = bool(row.has_statistics)
        for endpoint, requires_nonempty in ENDPOINT_REQUIRES_NONEMPTY.items():
            covered[lc][endpoint][fid] = has_stats if requires_nonempty else True

    # Convert defaultdicts to plain dicts so downstream code cannot rely on
    # auto-create behaviour (a missing key should raise KeyError).
    return {lc: dict(endpoints) for lc, endpoints in covered.items()}


def covered_for_league(
    all_covered: dict[str, dict[str, dict[int, bool]]],
    league_code: str,
    *,
    kickoff_by_id: dict[int, date] | None = None,
) -> dict[str, set[int]]:
    """Return the fixture IDs that should be skipped this run, keyed by shell key.

    Translates endpoint names (LINEUPS, FIXTURE_EVENTS, ...) to the shell keys
    (lineups, events, ...) used throughout the fanout scheduler, so the rest of
    the fanout code does not need to know about endpoint naming.

    Returns a dict with all four shell keys, each mapping to the set of fixture
    IDs that should NOT be re-fetched. A fixture is excluded from the skip set
    (i.e. will be re-fetched) only when all of the following hold:
      - The endpoint is FIXTURE_STATISTICS
      - has_data is False (previous fetch returned an empty statistics payload)
      - The fixture's kickoff date is known and within STATS_GRACE_DAYS of today

    For all other cases — has_data=True, non-statistics endpoints, or missing
    kickoff date — the fixture is conservatively added to the skip set.

    kickoff_by_id maps fixture_id → kickoff date (UTC calendar day). When omitted,
    the grace-period logic is skipped and all coverage entries are treated as final.
    """
    league_coverage = all_covered.get(league_code, {})
    today = datetime.now(timezone.utc).date()
    result: dict[str, set[int]] = {}

    for shell_key, endpoint in SHELL_KEY_TO_ENDPOINT.items():
        endpoint_data: dict[int, bool] = league_coverage.get(endpoint, {})
        skip_set: set[int] = set()

        for fid, has_data in endpoint_data.items():
            if has_data:
                # Data received — never re-fetch.
                skip_set.add(fid)
            elif endpoint == "FIXTURE_STATISTICS" and kickoff_by_id is not None:
                kickoff = kickoff_by_id.get(fid)
                if kickoff is not None and (today - kickoff).days < STATS_GRACE_DAYS:
                    # Empty response but still within the delivery-delay grace period.
                    # Omit from skip_set so the fixture is retried this run.
                    pass
                else:
                    # Grace period elapsed (or kickoff unknown) — stop retrying.
                    skip_set.add(fid)
            else:
                # Non-statistics endpoint, or no kickoff info — skip conservatively.
                skip_set.add(fid)

        result[shell_key] = skip_set

    return result
