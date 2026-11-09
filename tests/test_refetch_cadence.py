"""Tests for the 7-day re-fetch cadence of transfers and coaches and its sources.yml thresholds."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.api_football.refetch import (  # noqa: E402
    FRESHNESS_MUST_EXCEED_CADENCE_BY_DAYS,
    REFETCH_INTERVAL_DAYS,
    latest_ingest_per_league,
    next_due,
    should_refetch,
    stagger_offset_days,
)

REPO = Path(__file__).resolve().parents[1]
SOURCES_YML = REPO / "dbt_project" / "models" / "1_staging" / "api_football" / "sources.yml"

# TRANSFERS is read latest-per-league, so a partial write hides the complete row downstream;
# COACHES is read across all snapshots, so a partial write only adds noise that base dedups away.
CADENCED_TABLES = {"RAW_APIF_TRANSFERS", "RAW_APIF_COACHES"}

NOW = datetime(2026, 8, 10, 4, 0, tzinfo=timezone.utc)


def test_a_league_ingested_today_is_skipped():
    assert not should_refetch("BL1", NOW - timedelta(hours=6), NOW)


def test_a_league_ingested_long_ago_is_refetched():
    assert should_refetch("BL1", NOW - timedelta(days=REFETCH_INTERVAL_DAYS + 1), NOW)


def test_a_league_never_ingested_is_always_fetched():
    """Skipping a never-ingested league would leave it permanently absent from raw."""
    assert should_refetch("BL1", None, NOW)


def test_the_force_flag_overrides_the_cadence(monkeypatch):
    fresh = NOW - timedelta(hours=1)
    assert not should_refetch("BL1", fresh, NOW)
    monkeypatch.setenv("API_FOOTBALL_INGEST_FORCE_FULL", "1")
    assert should_refetch("BL1", fresh, NOW)


def test_the_stagger_spreads_leagues_across_the_whole_interval():
    """Leagues share tonight's ingested_at, so without a stagger they all come due together."""
    codes = ["BL1", "BL2", "PL", "PD", "SA", "L1", "VL", "WC", "LMX", "LP", "MLS", "SPL",
             "ED", "UCL", "UEL", "UECL", "BSA", "APD", "J1", "KL1", "DFBP", "FAC"]
    offsets = {c: stagger_offset_days(c) for c in codes}
    assert all(0 <= o < REFETCH_INTERVAL_DAYS for o in offsets.values())
    assert len(set(offsets.values())) >= 5, (
        f"offsets barely spread: {sorted(set(offsets.values()))}. All leagues would come due "
        "on nearly the same night, which is the spike this exists to prevent."
    )


def test_the_stagger_is_stable_across_processes():
    """Python salts the builtin `hash()` per process, so a league's offset must not depend on it."""
    assert stagger_offset_days("BL1") == stagger_offset_days("BL1")
    assert [stagger_offset_days(c) for c in ("BL1", "PL", "SA")] == [
        stagger_offset_days(c) for c in ("BL1", "PL", "SA")
    ]


@pytest.mark.parametrize("code", ["BL1", "PL", "SA", "WC", "MLS", "J1", "FAC", "UCL"])
def test_every_league_actually_gets_the_ruled_cadence(code):
    """A year of nightly runs must show exactly the interval between re-fetches for every league."""
    last = datetime(2026, 1, 1, 4, 0, tzinfo=timezone.utc)
    fetches = []
    for day in range(365):
        now = datetime(2026, 1, 1, 4, 0, tzinfo=timezone.utc) + timedelta(days=day)
        if should_refetch(code, last, now):
            fetches.append(now)
            last = now

    assert len(fetches) >= 40, f"{code} barely re-fetched in a year: {len(fetches)}"
    gaps = {(b - a).days for a, b in zip(fetches, fetches[1:])}
    assert gaps == {REFETCH_INTERVAL_DAYS}, (
        f"{code} re-fetched at gaps of {sorted(gaps)} days; the CPO ruled exactly "
        f"{REFETCH_INTERVAL_DAYS}. A stagger must shift WHICH day, never how often."
    )


@pytest.mark.parametrize("code", ["BL1", "PL", "SA", "WC", "MLS"])
def test_the_logged_next_due_date_is_the_day_it_actually_refetches(code):
    """The date `next_due` reports must be the first day `should_refetch` returns True."""
    last = datetime(2026, 3, 2, 4, 0, tzinfo=timezone.utc)
    reported = next_due(last, code)

    actual = None
    for day in range(1, REFETCH_INTERVAL_DAYS + 2):
        now = last + timedelta(days=day)
        if should_refetch(code, last, now):
            actual = now
            break

    assert actual is not None, f"{code} never became due within a full cycle"
    assert reported.date() == actual.date(), (
        f"{code}: the skip log would report {reported.date()} but the scheduler re-fetches on "
        f"{actual.date()}."
    )


def test_the_stagger_actually_spreads_the_load_across_the_week():
    codes = ["BL1", "BL2", "PL", "PD", "SA", "L1", "VL", "WC", "LMX", "LP", "MLS", "SPL",
             "ED", "UCL", "UEL", "UECL", "BSA", "APD", "J1", "KL1", "DFBP", "FAC"]
    last = {c: datetime(2026, 1, 1, 4, 0, tzinfo=timezone.utc) for c in codes}
    per_day = []
    for day in range(1, 15):
        now = datetime(2026, 1, 1, 4, 0, tzinfo=timezone.utc) + timedelta(days=day)
        due = [c for c in codes if should_refetch(c, last[c], now)]
        for c in due:
            last[c] = now
        per_day.append(len(due))

    busiest = max(per_day)
    assert busiest < len(codes), (
        f"all {len(codes)} leagues came due on one night ({per_day}); that is the spike the "
        "stagger exists to prevent."
    )
    assert busiest <= len(codes) // 2, f"load poorly spread across the week: {per_day}"


def test_a_failed_cadence_read_makes_every_league_due():
    """A failed cadence read fails toward fetching, since skipping forever would rot the data."""
    class _Boom:
        def query(self, _sql):
            raise RuntimeError("BigQuery unavailable")

    assert latest_ingest_per_league(_Boom(), "RAW_APIF_TRANSFERS") == {}
    assert should_refetch("BL1", {}.get("BL1"), NOW)


def test_a_skipped_league_writes_nothing_at_all(monkeypatch):
    """A skip neither fetches nor writes, since a partial write hides the latest-per-league row."""
    from ingestion.api_football.loads import competition_runner as cr

    calls = []
    monkeypatch.setattr(cr, "load_transfers_batch", lambda *a, **k: calls.append(a))

    result = type("R", (), {"league_code": "BL1", "team_ids": {1, 2}, "seasons_list": [2026]})()
    ctx = _FakeCtx()

    fresh = {"BL1": datetime.now(timezone.utc) - timedelta(hours=2)}
    cr.run_transfers_for_competition(ctx, result, transfers_last_ingest=fresh)
    assert calls == [], "a skipped league still called the loader; it would write a partial row"

    stale = {"BL1": datetime.now(timezone.utc) - timedelta(days=30)}
    cr.run_transfers_for_competition(ctx, result, transfers_last_ingest=stale)
    assert len(calls) == 1, "a due league did not fetch; the cadence would never refresh"

    # run_transfers_for_competition swallows every exception, so the empty error sink is the check.
    assert ctx.errors == [], f"the run path raised and it was swallowed: {ctx.errors}"


class _FakeCtx:
    """Stands in for PipelineContext with the surface run_transfers_for_competition uses."""

    def __init__(self):
        self.errors: list[str] = []
        self.skipped_per_team: set[str] = set()

    def record_skipped(self, league_code: str, entity: str) -> None:
        self.skipped_per_team.add(f"{league_code}/{entity}")


def test_a_skipped_league_is_recorded_for_the_completeness_gate(monkeypatch):
    """A skipped league cannot heal a persistent gap, so the skip is recorded for the gate."""
    from ingestion.api_football.loads import competition_runner as cr

    monkeypatch.setattr(cr, "load_transfers_batch", lambda *a, **k: None)
    result = type("R", (), {"league_code": "UCL", "team_ids": {1}, "seasons_list": [2026]})()

    skipped_ctx = _FakeCtx()
    fresh = {"UCL": datetime.now(timezone.utc) - timedelta(hours=2)}
    cr.run_transfers_for_competition(skipped_ctx, result, transfers_last_ingest=fresh)
    assert skipped_ctx.skipped_per_team == {"UCL/TRANSFERS"}, (
        "a skipped league was not recorded, so the completeness gate cannot tell a deliberate "
        "skip from a stalled ingest and will hard-fail the run"
    )
    assert skipped_ctx.errors == []

    # A league that is fetched must not be exempted, or the gate goes blind.
    fetched_ctx = _FakeCtx()
    stale = {"UCL": datetime.now(timezone.utc) - timedelta(days=30)}
    cr.run_transfers_for_competition(fetched_ctx, result, transfers_last_ingest=stale)
    assert fetched_ctx.skipped_per_team == set(), (
        "a league that was actually fetched was marked skipped; its gaps would stop gating"
    )


def test_no_cadence_information_means_fetch(monkeypatch):
    """The default of None must fetch, or a caller omitting the argument stops ingesting."""
    from ingestion.api_football.loads import competition_runner as cr

    calls = []
    monkeypatch.setattr(cr, "load_transfers_batch", lambda *a, **k: calls.append(a))
    result = type("R", (), {"league_code": "BL1", "team_ids": {1}, "seasons_list": [2026]})()
    ctx = type("C", (), {"errors": []})()

    cr.run_transfers_for_competition(ctx, result)
    assert len(calls) == 1


def _threshold_days(spec: dict) -> float:
    per = {"minute": 1 / 1440, "hour": 1 / 24, "day": 1}
    return float(spec["count"]) * per[spec["period"]]


@pytest.mark.parametrize("table", sorted(CADENCED_TABLES))
def test_freshness_thresholds_exceed_the_cadence(table):
    """`error_after` must exceed the cadence plus one cycle, or the hourly sentinel alerts daily."""
    doc = yaml.safe_load(SOURCES_YML.read_text(encoding="utf-8"))
    tables = {
        (t.get("identifier") or t["name"]): t
        for s in doc["sources"] for t in s["tables"]
    }
    assert table in tables, f"{table} vanished from sources.yml"
    fresh = tables[table].get("freshness")
    assert fresh, f"{table} lost its freshness block; the sentinel would stop checking it"

    error_days = _threshold_days(fresh["error_after"])
    minimum = REFETCH_INTERVAL_DAYS + FRESHNESS_MUST_EXCEED_CADENCE_BY_DAYS
    assert error_days > minimum, (
        f"{table} error_after is {error_days}d but the re-fetch cadence is "
        f"{REFETCH_INTERVAL_DAYS}d. It must exceed {minimum}d (cadence + one cycle), or the "
        "staleness alert fires daily on a pipeline that is behaving correctly, and gets muted."
    )

    warn_days = _threshold_days(fresh["warn_after"])
    assert warn_days >= REFETCH_INTERVAL_DAYS, (
        f"{table} warn_after is {warn_days}d, inside the {REFETCH_INTERVAL_DAYS}d cadence — "
        "it would warn on every normal cycle."
    )
    assert warn_days < error_days


def test_the_nightly_sources_keep_their_tight_thresholds():
    """Only the cadenced tables may have relaxed thresholds; the rest are ingested nightly."""
    doc = yaml.safe_load(SOURCES_YML.read_text(encoding="utf-8"))
    for s in doc["sources"]:
        for t in s["tables"]:
            name = t.get("identifier") or t["name"]
            fresh = t.get("freshness")
            if not fresh or name in CADENCED_TABLES:
                continue
            assert _threshold_days(fresh["error_after"]) <= 3, (
                f"{name} is not on a re-fetch cadence but its error_after was widened to "
                f"{_threshold_days(fresh['error_after'])}d. Only the cadenced tables may relax."
            )
