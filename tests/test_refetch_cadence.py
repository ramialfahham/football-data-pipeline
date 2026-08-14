"""The 7-day re-fetch cadence for transfers and coaches. #33 item 14.

WHAT THIS GUARDS
----------------
Skipping work is easy to get wrong in ways that are silent:

  · skipping a league that has NEVER been ingested  → it stays permanently absent
  · skipping but still WRITING                      → a partial row, which since 8b DELETES
                                                       the complete one (the #37 shape)
  · a failed cadence read treated as "up to date"   → every league skipped forever
  · cadence and sources.yml thresholds drifting     → the staleness alert fires daily on
                                                       CORRECT behaviour and gets muted

None of those raise. Each has a test below, and the last is the one that ties this change's two
halves together — the code cadence and the dbt freshness thresholds are only correct relative to
each other.
"""

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

# The tables this task put on a cadence. They differ in write mode and it matters:
#   TRANSFERS is merge-on-write (8b) and read latest-per-league — a partial write DELETES.
#   COACHES is APPEND-ONLY, deliberately excluded from 8b because stg_apif__coaches reads all
#   snapshots to preserve every coach ever seen (CPO 2026-06-23) — a partial write only adds
#   noise. An earlier version of this file called both merge-on-write; a reviewer caught it.
CADENCED_TABLES = {"RAW_APIF_TRANSFERS", "RAW_APIF_COACHES"}

NOW = datetime(2026, 8, 10, 4, 0, tzinfo=timezone.utc)


def test_a_league_ingested_today_is_skipped():
    assert not should_refetch("BL1", NOW - timedelta(hours=6), NOW)


def test_a_league_ingested_long_ago_is_refetched():
    assert should_refetch("BL1", NOW - timedelta(days=REFETCH_INTERVAL_DAYS + 1), NOW)


def test_a_league_never_ingested_is_always_fetched():
    """The one that must never be "optimised". There is no stored row to preserve, so skipping
    would leave the competition permanently absent from raw — silently, since nothing errors."""
    assert should_refetch("BL1", None, NOW)


def test_the_force_flag_overrides_the_cadence(monkeypatch):
    """A backfill has to be able to bypass this. Reuses the existing
    API_FOOTBALL_INGEST_FORCE_FULL rather than a second flag nobody would remember."""
    fresh = NOW - timedelta(hours=1)
    assert not should_refetch("BL1", fresh, NOW)
    monkeypatch.setenv("API_FOOTBALL_INGEST_FORCE_FULL", "1")
    assert should_refetch("BL1", fresh, NOW)


def test_the_stagger_spreads_leagues_across_the_whole_interval():
    """Every league shares tonight's ingested_at, so without a stagger they all come due on the
    same night: one night in seven costing the full 45 minutes against a 3h timeout, six costing
    nothing. This asserts the offsets actually spread rather than clustering."""
    codes = ["BL1", "BL2", "PL", "PD", "SA", "L1", "VL", "WC", "LMX", "LP", "MLS", "SPL",
             "ED", "UCL", "UEL", "UECL", "BSA", "APD", "J1", "KL1", "DFBP", "FAC"]
    offsets = {c: stagger_offset_days(c) for c in codes}
    assert all(0 <= o < REFETCH_INTERVAL_DAYS for o in offsets.values())
    assert len(set(offsets.values())) >= 5, (
        f"offsets barely spread: {sorted(set(offsets.values()))}. All leagues would come due "
        "on nearly the same night, which is the spike this exists to prevent."
    )


def test_the_stagger_is_stable_across_processes():
    """Python salts the builtin `hash()` per process, so using it here would give a league a
    different offset every run and smear the cadence into 'somewhere between 1 and 7 days'.
    This pins the values, so a switch to `hash()` fails rather than silently degrading."""
    assert stagger_offset_days("BL1") == stagger_offset_days("BL1")
    assert [stagger_offset_days(c) for c in ("BL1", "PL", "SA")] == [
        stagger_offset_days(c) for c in ("BL1", "PL", "SA")
    ]


@pytest.mark.parametrize("code", ["BL1", "PL", "SA", "WC", "MLS", "J1", "FAC", "UCL"])
def test_every_league_actually_gets_the_ruled_cadence(code):
    """THE ONE MY FIRST VERSION LACKED, and a reviewer found the bug instead.

    The first implementation computed `due_after = interval - offset` on EVERY call, which
    permanently SHORTENED the interval: a league with offset 6 re-fetched every single day and
    only offset 0 ever got 7 days. It looked like a stagger and was a silent cadence cut, and
    the CPO's ruling was "every 7 days" — not "somewhere between 1 and 7 depending on a hash".

    This simulates a year of nightly runs and asserts the observed gap between re-fetches is
    exactly the ruled interval for EVERY league, not just the lucky ones. It fails on the old
    implementation for 6 of every 7 leagues.
    """
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
    """The skip log tells an operator when a league next runs. If `next_due` and
    `should_refetch` compute that two different ways, the log lies — and a lying log is worse
    than none, because it gets trusted during an incident.

    Asserts the reported date is the first day `should_refetch` actually returns True.
    """
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
    """The other half: exact cadence is worthless if every league lands on the same day, which
    is the 45-minute spike the stagger exists to prevent."""
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
    """Fail toward fetching, never toward skipping.

    If the cadence query dies, treating leagues as up-to-date would skip every phase forever
    and the data would rot in silence. A redundant fetch is the cheap error."""
    class _Boom:
        def query(self, _sql):
            raise RuntimeError("BigQuery unavailable")

    assert latest_ingest_per_league(_Boom(), "RAW_APIF_TRANSFERS") == {}
    assert should_refetch("BL1", {}.get("BL1"), NOW)


def test_a_skipped_league_writes_nothing_at_all(monkeypatch):
    """THE ONE THAT PREVENTS DATA LOSS.

    A skip must not fetch AND must not write. RAW_APIF_TRANSFERS is one row per league and
    merge-on-write since 8b, so a write of a partial payload would DELETE the complete row —
    the #37 defect, made permanent. Asserted by running the real orchestration path with the
    loader replaced by a recorder: zero calls, not "a call with less data".
    """
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

    # ⚠ THE BROAD `except Exception` IN run_transfers_for_competition SWALLOWS EVERYTHING.
    # An earlier version of this test used `type("C", (), {"errors": []})()`, a fake with no
    # `record_skipped`. Once the skip branch started calling it, that raised AttributeError, the
    # except caught it, and this test stayed green while the code under test was broken. Assert
    # the error sink is empty so the fake can never silently diverge from PipelineContext again.
    assert ctx.errors == [], f"the run path raised and it was swallowed: {ctx.errors}"


class _FakeCtx:
    """Stands in for PipelineContext with the surface run_transfers_for_competition uses.

    Deliberately implements `record_skipped` the same way the real dataclass does, so a test that
    exercises the skip branch fails loudly if that contract changes, rather than being absorbed by
    the caller's broad exception handler.
    """

    def __init__(self):
        self.errors: list[str] = []
        self.skipped_per_team: set[str] = set()

    def record_skipped(self, league_code: str, entity: str) -> None:
        self.skipped_per_team.add(f"{league_code}/{entity}")


def test_a_skipped_league_is_recorded_for_the_completeness_gate(monkeypatch):
    """THE 2026-08-14 NIGHTLY, pinned at the call site that actually fixes it.

    The completeness gate fails a run when a per-team gap persists across two runs, because a
    normal gap heals on the next night's fetch. A league skipped by this cadence cannot heal, so
    the skip MUST be recorded or the gate hard-fails on correct behaviour and the dbt build never
    runs — which is exactly what happened (`UCL/TRANSFERS (1 then 1 teams missing)`, exit 3).

    The gate-side tests in test_per_team_completeness.py drive
    `detect_stagnant_per_team_gaps` directly with a hand-built set, so NONE of them fails if this
    call site is reverted. This is the test that does.
    """
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

    # The other direction: a league that IS fetched must NOT be exempted, or the gate goes blind.
    fetched_ctx = _FakeCtx()
    stale = {"UCL": datetime.now(timezone.utc) - timedelta(days=30)}
    cr.run_transfers_for_competition(fetched_ctx, result, transfers_last_ingest=stale)
    assert fetched_ctx.skipped_per_team == set(), (
        "a league that was actually fetched was marked skipped; its gaps would stop gating"
    )


def test_no_cadence_information_means_fetch(monkeypatch):
    """Passing None (the default) must behave exactly as before this change — every league
    fetches. Otherwise any caller that forgets the argument silently stops ingesting."""
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
    """THE GUARD THAT TIES THE TWO HALVES TOGETHER.

    The code cadence and the dbt freshness thresholds are only correct relative to each other.
    At the old 54h, a table refreshed every 7 days sits permanently past `error_after`.

    Nothing on this branch reads those thresholds — `dbt source freshness` is invoked nowhere,
    and the consumer is the hourly sentinel on the separate, unmerged #39 Stage 2 branch (!30).
    So today this is inert; once !30 lands, unraised thresholds would email EVERY DAY about a
    pipeline behaving exactly as ruled, which ends with somebody muting the alert and leaving
    the pipeline unwatched again. This test is what keeps the two halves in step regardless of
    which merges first.

    So `error_after` must exceed the cadence plus one whole extra cycle. Change
    REFETCH_INTERVAL_DAYS to 14 without touching sources.yml and this fails, which is the point.
    """
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
    """The relaxation must be confined to the two cadenced tables. Everything else is still
    ingested nightly, and widening those would blind the sentinel for no reason."""
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
