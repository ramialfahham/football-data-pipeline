"""The out-of-band staleness sentinel. GitLab #39 Stage 2.

WHAT IT GUARDS
--------------
`scripts/check_raw_freshness.py` is the ONLY thing in this system that can notice the nightly
has stopped. Every other check runs inside the nightly, so a nightly that never runs takes its
own monitoring with it — which is exactly how six days of stale data passed unnoticed in
August 2026.

That makes the sentinel's failure modes unusually expensive, and they are all quiet ones:

  · returning 0 when a source is stale        → the outage stays invisible, as before
  · returning 0 when it could not check       → a broken sentinel looks like a healthy pipeline
  · inventing a threshold for a source that
    deliberately has none                      → false alarms, and an alert people learn to mute

None of those raise. Each test below targets one, and the pure `evaluate()` split exists so
they can be driven without BigQuery.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_raw_freshness import (  # noqa: E402
    evaluate,
    load_thresholds,
    main,
)

REPO = Path(__file__).resolve().parents[1]
SOURCES_YML = REPO / "dbt_project" / "models" / "1_staging" / "api_football" / "sources.yml"


def test_thresholds_come_from_sources_yml_and_match_it():
    """The sentinel must not carry its own copy of the thresholds.

    Two definitions drift, and the drifted one is the one nobody notices. This asserts the
    loader returns exactly the tables that declare a `freshness:` block in the real file — not
    a hardcoded list that would quietly stop matching when a source is added.
    """
    doc = yaml.safe_load(SOURCES_YML.read_text(encoding="utf-8"))
    expected = {
        (t.get("identifier") or t["name"])
        for s in doc["sources"] for t in s["tables"] if t.get("freshness")
    }
    assert load_thresholds() .keys() == expected, (
        "the sentinel's table set diverged from sources.yml. It must be derived, never listed."
    )
    assert expected, "sources.yml declares no freshness thresholds; the sentinel would no-op."


def test_sources_without_a_threshold_are_never_checked():
    """3 of the 11 sources deliberately carry `loaded_at_field` but NO thresholds — they
    refresh rarely and any threshold would false-alarm. Checking them anyway is how a sentinel
    starts crying wolf and gets muted, which is worse than not having one."""
    doc = yaml.safe_load(SOURCES_YML.read_text(encoding="utf-8"))
    without = {
        (t.get("identifier") or t["name"])
        for s in doc["sources"] for t in s["tables"]
        if t.get("loaded_at_field") and not t.get("freshness")
    }
    assert without, "expected some sources to be deliberately threshold-free; sources.yml changed"
    assert not (without & load_thresholds().keys()), (
        f"the sentinel would check {sorted(without & load_thresholds().keys())}, which "
        "deliberately have no thresholds."
    )


def test_a_stale_source_is_reported_stale():
    thresholds = {"T": {"error_after_hours": 54.0, "warn_after_hours": 30.0}}
    stale, warning = evaluate({"T": 55.0}, thresholds)
    assert [t for t, _, _ in stale] == ["T"], "a source past error_after was not flagged stale"
    assert not warning


def test_a_fresh_source_is_neither_stale_nor_warned():
    thresholds = {"T": {"error_after_hours": 54.0, "warn_after_hours": 30.0}}
    stale, warning = evaluate({"T": 1.0}, thresholds)
    assert not stale and not warning


def test_a_warning_is_not_an_error():
    """warn_after must NOT fail the job. If it did, every run 30h after the last ingest would
    page — and the nightly is daily, so that would be routine."""
    thresholds = {"T": {"error_after_hours": 54.0, "warn_after_hours": 30.0}}
    stale, warning = evaluate({"T": 31.0}, thresholds)
    assert not stale, "a warn-level age was escalated to stale; this would page routinely"
    assert [t for t, _, _ in warning] == ["T"]


def test_the_boundary_is_strictly_greater_than():
    """Exactly at the threshold is not yet stale. Off-by-one here means a daily alert."""
    thresholds = {"T": {"error_after_hours": 54.0}}
    assert not evaluate({"T": 54.0}, thresholds)[0]
    assert evaluate({"T": 54.01}, thresholds)[0]


def _install_healthy_bigquery(monkeypatch):
    """A BigQuery that always answers, and answers FRESH.

    Needed so `main()` can only return 2 via the branch under test. Without it this test was
    masked: `test:python` in CI runs with no GCP credentials (the job merges `<<: *python`
    only, no `*gcp_job`, no `id_tokens:`), so `bigquery.Client()` raises, `main()` returns 2
    through the "BigQuery unavailable" branch, and the assertion held whether or not the defect
    it names had been reintroduced — the same "silently exercises the wrong thing" class this
    file warns about elsewhere, applied to this file itself.
    """
    class _Meta:
        modified = datetime.now(timezone.utc)

    class _Client:
        def __init__(self, *a, **k):
            pass

        def get_table(self, _ref):
            return _Meta()

    import google.cloud.bigquery as bq

    monkeypatch.setattr(bq, "Client", _Client)


def test_a_sentinel_that_cannot_read_its_thresholds_does_not_report_healthy(monkeypatch, tmp_path):
    """THE most dangerous failure mode: exit 0 while checking nothing.

    A sentinel that cannot check must never look healthy — that is indistinguishable from a
    working pipeline, which is the precise shape of the incident this whole stage exists to
    prevent. Exit 2, not 0.

    BigQuery is stubbed HEALTHY on purpose. If `load_thresholds` regressed to binding
    `SOURCES_YML` as an import-time default (the defect this pins), the monkeypatched path would
    be ignored, the real sources.yml would load, every table would read as fresh, and `main()`
    would return 0 — so the assertion fails, which is what it is for. Without the stub, an
    unauthenticated environment returns 2 for an unrelated reason and hides that entirely.
    """
    import scripts.check_raw_freshness as mod

    _install_healthy_bigquery(monkeypatch)
    monkeypatch.setattr(mod, "SOURCES_YML", tmp_path / "does-not-exist.yml")
    assert main([]) == 2, "an unreadable thresholds file reported success"


def test_an_empty_threshold_set_does_not_report_healthy(monkeypatch):
    """Same class: if sources.yml parses but declares nothing, there is nothing to check and
    saying OK would be a lie."""
    import scripts.check_raw_freshness as mod

    _install_healthy_bigquery(monkeypatch)  # so 2 can only come from the branch under test
    monkeypatch.setattr(mod, "load_thresholds", lambda *a, **k: {})
    assert main([]) == 2, "an empty threshold set reported success"


@pytest.mark.parametrize("age_hours, expected_exit", [(1.0, 0), (100.0, 1)])
def test_end_to_end_exit_code_drives_the_alert(monkeypatch, age_hours, expected_exit):
    """The exit code IS the alerting mechanism — Cloud Run marks a non-zero execution FAILED
    and the alert policy fires on that. Asserted end to end through main(), with BigQuery
    replaced, because an exit code that is right in evaluate() and wrong in main() alerts on
    nothing."""
    import scripts.check_raw_freshness as mod

    monkeypatch.setattr(mod, "load_thresholds", lambda *a, **k: {"T": {"error_after_hours": 54.0}})

    class _FakeMeta:
        modified = datetime.now(timezone.utc) - timedelta(hours=age_hours)

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        def get_table(self, _ref):
            return _FakeMeta()

    import google.cloud.bigquery as bq

    monkeypatch.setattr(bq, "Client", _FakeClient)
    assert main([]) == expected_exit


def test_an_unreadable_table_is_not_treated_as_fresh(monkeypatch):
    """A table BigQuery will not answer for is unknown, not fresh. Returning 0 here would mean
    a deleted or renamed raw table silently reads as healthy forever."""
    import scripts.check_raw_freshness as mod

    monkeypatch.setattr(mod, "load_thresholds", lambda *a, **k: {"T": {"error_after_hours": 54.0}})

    class _Boom:
        def __init__(self, *a, **k):
            pass

        def get_table(self, _ref):
            raise RuntimeError("404 Not found: Table T")

    import google.cloud.bigquery as bq

    monkeypatch.setattr(bq, "Client", _Boom)
    assert main([]) == 2, "an unreadable table reported success"
