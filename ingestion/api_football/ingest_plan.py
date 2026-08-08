"""Per-competition ingest mode: full (all phases) vs poll (catalog + latest-season fixtures only).

Decided from BigQuery state before spending API quota. Competition-agnostic.
"""

from __future__ import annotations

import os
from typing import Literal

from google.cloud import bigquery

from .bigquery import read_latest_payload_json
from .completeness import (
    FINISHED_STATUS_SHORT,
    _fixture_ids_from_fixtures_payload,
)
# read_coverage is deliberately NOT imported here. This module is reached once per
# competition, so a call to it from this file is the O(competitions^2) defect #33 item 1
# removed. The caller reads coverage once and passes it in; `ruff` will flag the import
# as unused if someone adds it back without a call site.
from .coverage import covered_for_league
from .fixture_scheduling import (
    _coverage_for_season,
    _fixture_needs_any_endpoint,
)
from .registry import Competition
from .settings import raw_table

IngestMode = Literal["full", "poll"]

# Align with int_matchday__upcoming_round_fixtures (scheduled, not yet played).
UPCOMING_STATUS_SHORT = frozenset({"NS", "TBD"})


def _force_full_ingest() -> bool:
    return os.getenv("API_FOOTBALL_INGEST_FORCE_FULL", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def decide_ingest_mode(
    *,
    has_fixtures_payload: bool,
    upcoming_count: int,
    fanout_gaps_on_finished: bool,
    force_full: bool = False,
) -> tuple[IngestMode, str]:
    """Pure policy: full when there is work; poll when idle. Used by tests and resolve_ingest_mode."""
    if force_full:
        return "full", "API_FOOTBALL_INGEST_FORCE_FULL"
    if not has_fixtures_payload:
        return "full", "no_merged_fixtures_in_bq"
    if upcoming_count > 0:
        return "full", f"upcoming_fixtures={upcoming_count}"
    if fanout_gaps_on_finished:
        return "full", "finished_fanout_gaps"
    return "poll", "idle_complete"


def _reference_season(comp: Competition, fixtures_payload: dict | None) -> int:
    years: list[int] = []
    for item in (fixtures_payload or {}).get("response") or []:
        league = item.get("league") or {}
        y = league.get("season")
        if y is not None:
            try:
                years.append(int(y))
            except (TypeError, ValueError):
                continue
    if years:
        return max(years)
    if comp.current_season is not None:
        return int(comp.current_season)
    return 0


def _finished_fanout_has_gaps(
    all_covered: dict[str, dict[str, dict[int, bool]]],
    league_code: str,
    fixtures_payload: dict | None,
    cov: dict[str, bool],
) -> bool:
    """Does this league have finished fixtures still missing fanout data?

    Takes ALREADY-READ coverage rather than reading it. `read_coverage()` scans all of
    RAW_APIF_FIXTURE_DETAILS with no league or time filter, and this function is reached
    once per competition, so reading it here made ingestion reads O(competitions^2) —
    45 scans of a multi-GiB table per run. The caller reads once and passes the result in
    (#33 item 1). `covered_for_league` is a pure dict lookup, so this is now in-memory work.
    """
    finished_ids = _fixture_ids_from_fixtures_payload(
        fixtures_payload,
        statuses=FINISHED_STATUS_SHORT,
    )
    if not finished_ids:
        return False
    covered = covered_for_league(all_covered, league_code)
    for fixture_id in finished_ids:
        if _fixture_needs_any_endpoint(fixture_id, covered, cov, finished_ids):
            return True
    return False


def resolve_ingest_mode(
    client: bigquery.Client,
    comp: Competition,
    all_covered: dict[str, dict[str, dict[int, bool]]],
) -> tuple[IngestMode, str]:
    """Read latest raw payloads and return (mode, reason) for this competition.

    `all_covered` is the run's single `read_coverage()` result, read ONCE by the caller
    before the per-competition loop. It is a required argument on purpose: defaulting it
    to None and reading lazily here would silently restore the per-competition scan this
    change exists to remove (#33 item 1).
    """
    try:
        fx_payload = read_latest_payload_json(
            client, raw_table("FIXTURES_NEXT"), league_code=comp.league_code
        )
    except Exception:
        fx_payload = None

    has_fixtures = bool((fx_payload or {}).get("response"))
    upcoming_count = len(
        _fixture_ids_from_fixtures_payload(fx_payload, statuses=UPCOMING_STATUS_SHORT)
    )

    try:
        leagues_payload = read_latest_payload_json(
            client, raw_table("LEAGUES"), league_code=comp.league_code
        )
    except Exception:
        leagues_payload = None

    ref_season = _reference_season(comp, fx_payload)
    cov = (
        _coverage_for_season(leagues_payload, ref_season)
        if leagues_payload and ref_season
        else {}
    )
    fanout_gaps = _finished_fanout_has_gaps(all_covered, comp.league_code, fx_payload, cov)

    return decide_ingest_mode(
        has_fixtures_payload=has_fixtures,
        upcoming_count=upcoming_count,
        fanout_gaps_on_finished=fanout_gaps,
        force_full=_force_full_ingest(),
    )
