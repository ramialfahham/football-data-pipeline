"""Per-league re-fetch cadence for the loaders that do not need nightly data. #33 item 14.

WHY
---
`transfers` and `coaches` re-download identical data every night: 26.7 + 18.7 = 45 of the 105
ingestion minutes measured on the 2026-08-09 nightly, and roughly 3,800 of ~8,300 daily API
calls. Transfers move in bursts (January, summer); managers change rarely. CPO ruling: re-fetch
both every 7 days per league.

This is not restoring something that was lost. `git log -S` across all history shows neither
loader ever had skip-if-present logic. Five other loaders do — `players`, `player_squads`,
`player_profiles`, `player_teams`, `fixtures`, `fixture_details` — and these two never got it.

⚠ THE SKIP MUST SKIP THE WRITE, NOT JUST THE FETCH — for DIFFERENT reasons per table
------------------------------------------------------------------------------------
Both loaders write one row per league per run, so fetching a subset of teams and writing it
would persist a partial snapshot. What that costs differs, and an earlier version of this
docstring got COACHES wrong by asserting both were the same:

  RAW_APIF_TRANSFERS — `stg_apif__transfers` reads latest-per-league, so a partial write HIDES
  the complete snapshot from every model downstream. ⚠ It no longer DESTROYS it: this table was
  merge-on-write under #33 item 8b, and that was REVERSED on 2026-08-17 (CPO: raw appends and
  never deletes), so the complete row survives in raw and a bad write is recoverable by
  re-running rather than unrecoverable past time travel. The reason to keep the skip is
  unchanged — a hidden snapshot is still a wrong warehouse until the next good run.

  RAW_APIF_COACHES — the same, and it always was. `stg_apif__coaches` reads ALL snapshots to
  preserve every coach ever seen (CPO ruling 2026-06-23), so a partial write appends a thin
  snapshot that base then dedups. Coaches was the one table 8b never touched; since 2026-08-17
  every table has the property that used to make it special.

Either way a league that is not due is skipped ENTIRELY at the call site: no fetch, no write.
Its stored rows are untouched and staging reads exactly what it read yesterday. That is why no
carry-forward is needed here, unlike `loads/fixtures.py`, which carries prior seasons forward
precisely because it DOES write on every run.

READS ARE HOISTED
-----------------
`latest_ingest_per_league` is called ONCE per table per run and the result passed down, mirroring
`captured_player_team_seasons` (`orchestrator.py:201`). Calling it per competition would
reintroduce the O(competitions^2) shape that #33 item 1 removed.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone

from google.cloud import bigquery

from .settings import DATASET_ID, GCP_PROJECT_ID

# The CPO's ruling, in one place. Both loaders share it; a per-table cadence would be a second
# thing to keep in step with sources.yml for no benefit while the ruling covers both.
REFETCH_INTERVAL_DAYS = 7

# How many days the freshness thresholds in sources.yml must exceed the cadence before the
# staleness alert would fire on CORRECT behaviour. One whole extra cycle: a league refreshed on
# schedule is at most REFETCH_INTERVAL_DAYS old, and one missed run makes it 2x that.
# `tests/test_refetch_cadence.py` pins sources.yml against this so the two cannot drift.
FRESHNESS_MUST_EXCEED_CADENCE_BY_DAYS = 1


def _force_full() -> bool:
    """Reuse the existing backfill escape hatch rather than invent a second flag.

    `API_FOOTBALL_INGEST_FORCE_FULL` already means "ignore incremental shortcuts" elsewhere in
    the pipeline, and a backfill must be able to bypass the cadence.
    """
    return os.getenv("API_FOOTBALL_INGEST_FORCE_FULL", "").strip().lower() in ("1", "true", "yes")


def stagger_offset_days(league_code: str, interval_days: int = REFETCH_INTERVAL_DAYS) -> int:
    """A stable 0..interval-1 offset per league, so they do not all come due the same night.

    Without this every league shares tonight's `ingested_at` and therefore expires together:
    one night in seven costs the full 45 minutes against a 3h timeout, and the other six cost
    nothing. Spreading gives ~6-7 leagues a night. Each league still re-fetches every
    `interval_days` exactly as ruled; only the phase differs.

    md5 rather than `hash()`: Python salts `hash()` per process (PYTHONHASHSEED), so a league's
    offset would change on every run and the cadence would smear into "somewhere between 1 and 7
    days". Stability across processes is the whole point.
    """
    digest = hashlib.md5(league_code.encode("utf-8")).digest()
    return digest[0] % interval_days


def should_refetch(
    league_code: str,
    last_ingested: datetime | None,
    now: datetime,
    interval_days: int = REFETCH_INTERVAL_DAYS,
) -> bool:
    """Is this league due? Pure — no I/O, so the cadence is testable without BigQuery.

    True when the league has never been ingested (`last_ingested is None`), when the force flag
    is set, or when the row is older than its staggered due-date. A first-ever ingest must never
    be skipped: there is no row to keep, so skipping would leave the league permanently absent.
    """
    if _force_full():
        return True
    if last_ingested is None:
        return True

    age_days = (now - last_ingested).total_seconds() / 86400.0

    # SAFETY NET FIRST: never let a league exceed the ruled cadence, whatever the stagger says.
    # This is what makes a missed run self-heal instead of waiting a further week.
    if age_days >= interval_days:
        return True

    # Already refreshed today — never fetch a league twice in one day.
    if age_days < 1:
        return False

    # The stagger is a SLOT IN THE CALENDAR, not a shortened interval. Each league is due on
    # exactly one day in every `interval_days`, chosen by its own offset, so every league gets
    # the full cadence the CPO ruled and the work spreads across the week.
    #
    # An earlier version computed `due_after = interval_days - offset` on every call, which
    # looked equivalent and was not: it PERMANENTLY shortened the interval, so a league with
    # offset 6 re-fetched every single day and only offset 0 ever got 7 days. Caught in review.
    # The comment then claimed the offset "shifts the FIRST due-date only" — which is exactly
    # what this version does and the old one did not.
    return (now.toordinal() + stagger_offset_days(league_code, interval_days)) % interval_days == 0


def latest_ingest_per_league(
    client: bigquery.Client, table_name: str
) -> dict[str, datetime]:
    """`{league_code: latest ingested_at}` for one raw table. ONE query per table per run.

    Hoisted deliberately — see the module docstring. Returns an empty dict when the table does
    not exist or the read fails, which makes every league look never-ingested and therefore
    DUE. That is the safe direction: a failed read costs a redundant fetch, never a silent
    skip that would let data quietly go stale.
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
    """The next calendar day this league is due, derived the SAME way `should_refetch` decides.

    Two functions computing a due-date two ways is how a log line starts lying about what the
    scheduler will do, so this walks forward day by day using the same slot arithmetic rather
    than restating it as a formula.
    """
    offset = stagger_offset_days(league_code, interval_days)
    day = last_ingested + timedelta(days=1)
    for _ in range(interval_days + 1):
        if (day.toordinal() + offset) % interval_days == 0:
            return day
        day += timedelta(days=1)
    # Unreachable while a slot exists in every `interval_days` window; the safety net in
    # should_refetch would have fired by now anyway.
    return last_ingested + timedelta(days=interval_days)


def skip_reason(
    league_code: str,
    last_ingested: datetime | None,
    now: datetime,
    interval_days: int = REFETCH_INTERVAL_DAYS,
) -> str:
    """One log line explaining a skip, with the age and when it next runs.

    A skip that logs nothing is indistinguishable from a phase that silently stopped working —
    which is the failure class this repo has been bitten by twice.
    """
    if last_ingested is None:
        return "never ingested"
    age_h = (now - last_ingested).total_seconds() / 3600.0
    due = next_due(last_ingested, league_code, interval_days)
    return (f"age={age_h:.1f}h, next due {due:%Y-%m-%d} (cadence {interval_days}d)")


def utcnow() -> datetime:
    """Single clock source, so tests can freeze time by patching one name."""
    return datetime.now(timezone.utc)
