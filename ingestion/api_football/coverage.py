"""Derives which fixture endpoints already hold data from RAW_APIF_FIXTURE_DETAILS."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from collections import defaultdict

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .settings import GCP_PROJECT_ID, DATASET_ID, raw_table

# Days after kickoff during which an empty FIXTURE_STATISTICS response is retried.
STATS_GRACE_DAYS = 7

# The provider completes a match's player stats within three days of kickoff.
SECOND_FETCH_DELAY = timedelta(days=3)

# The provider's newer player-stats format never carries goals conceded or dribbled past, and the
# provider replaces it with the complete format for many matches only later.
NEWER_FORMAT_REFETCH_DELAY = timedelta(days=14)

# Value: the payload array that must be non-empty to count as covered, or None if any fetch counts.
ENDPOINT_REQUIRES_NONEMPTY: dict[str, str | None] = {
    "LINEUPS":            None,
    "FIXTURE_EVENTS":     None,
    "FIXTURE_STATISTICS": "statistics",
    "FIXTURE_PLAYERS":    None,
}

FANOUT_ENDPOINTS = tuple(ENDPOINT_REQUIRES_NONEMPTY.keys())

SHELL_KEY_TO_ENDPOINT: dict[str, str] = {
    "lineups":    "LINEUPS",
    "events":     "FIXTURE_EVENTS",
    "fx_stats":   "FIXTURE_STATISTICS",
    "fx_players": "FIXTURE_PLAYERS",
}

ENDPOINT_TO_SHELL_KEY: dict[str, str] = {v: k for k, v in SHELL_KEY_TO_ENDPOINT.items()}


def _fixture_details_table_id() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('FIXTURE_DETAILS')}"


def second_fetch_due(
    latest_fetch: datetime | None,
    kickoff: datetime | None,
    now: datetime,
) -> bool:
    """True once, when SECOND_FETCH_DELAY passes after a latest fetch that came before it."""
    if latest_fetch is None or kickoff is None:
        return False
    complete_from = kickoff + SECOND_FETCH_DELAY
    return latest_fetch < complete_from <= now


def newer_format_refetch_due(
    latest_fetch: datetime | None,
    kickoff: datetime | None,
    latest_in_newer_format: bool,
    now: datetime,
) -> bool:
    """True once, when NEWER_FORMAT_REFETCH_DELAY passes after a newer-format latest fetch."""
    if not latest_in_newer_format or latest_fetch is None or kickoff is None:
        return False
    refetch_from = kickoff + NEWER_FORMAT_REFETCH_DELAY
    return latest_fetch < refetch_from <= now


def read_coverage(
    client: bigquery.Client,
) -> dict[str, dict[str, dict[int, bool]]]:
    """covered[league_code][endpoint][fixture_id] = has_data, aggregated over a fixture's rows."""
    table_id = _fixture_details_table_id()

    try:
        client.get_table(table_id)
    except NotFound:
        return {}

    q = f"""
        WITH fetches AS (
            SELECT
                league_code,
                CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64) AS fixture_id,
                ARRAY_LENGTH(JSON_QUERY_ARRAY(payload, '$.statistics')) > 0 AS has_statistics,
                ingested_at,
                SAFE_CAST(JSON_VALUE(payload, '$.fixture.date') AS TIMESTAMP) AS kickoff,
                EXISTS(
                    SELECT 1
                    FROM UNNEST(JSON_QUERY_ARRAY(payload, '$.players')) AS team_block,
                        UNNEST(JSON_QUERY_ARRAY(team_block, '$.players')) AS player
                )
                AND NOT EXISTS(
                    SELECT 1
                    FROM UNNEST(JSON_QUERY_ARRAY(payload, '$.players')) AS team_block,
                        UNNEST(JSON_QUERY_ARRAY(team_block, '$.players')) AS player,
                        UNNEST(JSON_QUERY_ARRAY(player, '$.statistics')) AS stats
                    WHERE JSON_VALUE(stats, '$.goals.conceded') IS NOT NULL
                ) AS in_newer_format
            FROM `{table_id}`
            WHERE JSON_VALUE(payload, '$.fixture.id') IS NOT NULL
        )

        SELECT
            league_code,
            fixture_id,
            LOGICAL_OR(has_statistics) AS has_statistics,
            MAX(ingested_at) AS latest_fetch,
            MAX(kickoff) AS kickoff,
            ARRAY_AGG(in_newer_format ORDER BY ingested_at DESC LIMIT 1)[OFFSET(0)]
                AS latest_in_newer_format
        FROM fetches
        GROUP BY league_code, fixture_id
    """
    rows = list(client.query(q).result())

    now = datetime.now(timezone.utc)
    covered: dict[str, dict[str, dict[int, bool]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        lc = row.league_code
        fid = int(row.fixture_id)
        has_stats = bool(row.has_statistics)
        for endpoint, requires_nonempty in ENDPOINT_REQUIRES_NONEMPTY.items():
            covered[lc][endpoint][fid] = has_stats if requires_nonempty else True
        if second_fetch_due(row.latest_fetch, row.kickoff, now) or newer_format_refetch_due(
            row.latest_fetch, row.kickoff, bool(row.latest_in_newer_format), now
        ):
            covered[lc]["FIXTURE_PLAYERS"][fid] = False

    return {lc: dict(endpoints) for lc, endpoints in covered.items()}


def covered_for_league(
    all_covered: dict[str, dict[str, dict[int, bool]]],
    league_code: str,
    *,
    kickoff_by_id: dict[int, date] | None = None,
) -> dict[str, set[int]]:
    """Fixture ids to skip per shell key; only empty statistics inside STATS_GRACE_DAYS are retried.

    A due FIXTURE_PLAYERS second fetch is skipped too, so it never switches an idle competition
    to full mode.
    """
    league_coverage = all_covered.get(league_code, {})
    today = datetime.now(timezone.utc).date()
    result: dict[str, set[int]] = {}

    for shell_key, endpoint in SHELL_KEY_TO_ENDPOINT.items():
        endpoint_data: dict[int, bool] = league_coverage.get(endpoint, {})
        skip_set: set[int] = set()

        for fid, has_data in endpoint_data.items():
            if has_data:
                skip_set.add(fid)
            elif endpoint == "FIXTURE_STATISTICS" and kickoff_by_id is not None:
                kickoff = kickoff_by_id.get(fid)
                if kickoff is not None and (today - kickoff).days < STATS_GRACE_DAYS:
                    pass
                else:
                    skip_set.add(fid)
            else:
                skip_set.add(fid)

        result[shell_key] = skip_set

    return result
