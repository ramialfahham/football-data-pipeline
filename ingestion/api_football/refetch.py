"""Per-league re-fetch cadence for the transfers and coaches loaders.

A league that is not due is skipped entirely at the call site, no fetch and no write, because
writing a partial snapshot would hide the complete one from staging.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone

from google.cloud import bigquery

from .settings import DATASET_ID, GCP_PROJECT_ID

REFETCH_INTERVAL_DAYS = 7

# Days by which the sources.yml freshness thresholds must exceed the cadence, so the staleness
# alert does not fire on a league refreshed on schedule.
FRESHNESS_MUST_EXCEED_CADENCE_BY_DAYS = 1


def _force_full() -> bool:
    """`API_FOOTBALL_INGEST_FORCE_FULL` lets a backfill bypass the cadence."""
    return os.getenv("API_FOOTBALL_INGEST_FORCE_FULL", "").strip().lower() in ("1", "true", "yes")


def stagger_offset_days(league_code: str, interval_days: int = REFETCH_INTERVAL_DAYS) -> int:
    """A stable 0..interval-1 offset per league, so leagues do not all come due the same night.

    md5 rather than `hash()`, which Python salts per process and would change the offset every run.
    """
    digest = hashlib.md5(league_code.encode("utf-8")).digest()
    return digest[0] % interval_days


def should_refetch(
    league_code: str,
    last_ingested: datetime | None,
    now: datetime,
    interval_days: int = REFETCH_INTERVAL_DAYS,
) -> bool:
    """Whether this league is due; a first-ever ingest is never skipped."""
    if _force_full():
        return True
    if last_ingested is None:
        return True

    age_days = (now - last_ingested).total_seconds() / 86400.0

    # A missed run self-heals: no league exceeds the cadence whatever the stagger says.
    if age_days >= interval_days:
        return True

    if age_days < 1:
        return False

    # The stagger is a slot in the calendar, not a shortened interval: one due day per window.
    return (now.toordinal() + stagger_offset_days(league_code, interval_days)) % interval_days == 0


def latest_ingest_per_league(
    client: bigquery.Client, table_name: str
) -> dict[str, datetime]:
    """`{league_code: latest ingested_at}` for one raw table, read once per table per run.

    A missing table or failed read returns an empty dict, so every league is due: a redundant
    fetch, never a silent skip.
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    sql = f"""
        select league_code, max(ingested_at) as latest
        from `{table_id}`
        group by league_code
    """
    out: dict[str, datetime] = {}
    try:
        for row in client.query(sql).result():
            if row.league_code and row.latest:
                out[row.league_code] = row.latest
    except Exception:  # noqa: BLE001 - see docstring: fail toward fetching, never toward skipping
        return {}
    return out


def next_due(last_ingested: datetime, league_code: str,
             interval_days: int = REFETCH_INTERVAL_DAYS) -> datetime:
    """The next due day, walked forward with the same slot arithmetic as `should_refetch`."""
    offset = stagger_offset_days(league_code, interval_days)
    day = last_ingested + timedelta(days=1)
    for _ in range(interval_days + 1):
        if (day.toordinal() + offset) % interval_days == 0:
            return day
        day += timedelta(days=1)
    return last_ingested + timedelta(days=interval_days)


def skip_reason(
    league_code: str,
    last_ingested: datetime | None,
    now: datetime,
    interval_days: int = REFETCH_INTERVAL_DAYS,
) -> str:
    """One log line explaining a skip, with the age and when it next runs."""
    if last_ingested is None:
        return "never ingested"
    age_h = (now - last_ingested).total_seconds() / 3600.0
    due = next_due(last_ingested, league_code, interval_days)
    return (f"age={age_h:.1f}h, next due {due:%Y-%m-%d} (cadence {interval_days}d)")


def utcnow() -> datetime:
    """Single clock source, so tests can freeze time by patching one name."""
    return datetime.now(timezone.utc)
