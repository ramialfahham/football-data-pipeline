"""Tests for `scripts/check_raw_freshness.py`, the out-of-band sentinel for a stopped nightly."""

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
    """The sentinel derives its table set from sources.yml rather than keeping its own list."""
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
    """Sources with `loaded_at_field` but no thresholds refresh rarely, so one would false-alarm."""
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
    """`warn_after` must not fail the job, or every run 30h after the last ingest would page."""
    thresholds = {"T": {"error_after_hours": 54.0, "warn_after_hours": 30.0}}
    stale, warning = evaluate({"T": 31.0}, thresholds)
    assert not stale, "a warn-level age was escalated to stale; this would page routinely"
    assert [t for t, _, _ in warning] == ["T"]


def test_the_boundary_is_strictly_greater_than():
    thresholds = {"T": {"error_after_hours": 54.0}}
    assert not evaluate({"T": 54.0}, thresholds)[0]
    assert evaluate({"T": 54.01}, thresholds)[0]


def _install_healthy_bigquery(monkeypatch):
    """A BigQuery that always answers fresh, so `main()` returns 2 only via the branch tested."""
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
    """A sentinel that cannot check must exit 2, not 0; BigQuery is healthy here."""
    import scripts.check_raw_freshness as mod

    _install_healthy_bigquery(monkeypatch)
    monkeypatch.setattr(mod, "SOURCES_YML", tmp_path / "does-not-exist.yml")
    assert main([]) == 2, "an unreadable thresholds file reported success"


def test_an_empty_threshold_set_does_not_report_healthy(monkeypatch):
    """If sources.yml declares nothing, there is nothing to check and OK would be a lie."""
    import scripts.check_raw_freshness as mod

    _install_healthy_bigquery(monkeypatch)  # so 2 can only come from the branch under test
    monkeypatch.setattr(mod, "load_thresholds", lambda *a, **k: {})
    assert main([]) == 2, "an empty threshold set reported success"


@pytest.mark.parametrize("age_hours, expected_exit", [(1.0, 0), (100.0, 1)])
def test_end_to_end_exit_code_drives_the_alert(monkeypatch, age_hours, expected_exit):
    """Cloud Run marks a non-zero execution FAILED and the alert fires on that, so test `main()`."""
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
    """A table BigQuery will not answer for is unknown, not fresh."""
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
